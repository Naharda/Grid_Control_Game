"""Create a report-ready analysis package for modes/baseline_full.

The script uses every recorded result and game log for performance and
strategy analyses.  Because the experiment did not record elapsed time, it
also runs a small, explicitly labelled post-hoc decision-time benchmark on
six shared states reconstructed from the recorded games.

Run from the repository root:

    python analysis/baseline_full_report.py
"""

from __future__ import annotations

import csv
import json
import math
import os
import statistics
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".mplconfig"))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from experiments.modes import load_mode
from experiments.reconstruct_game import reconstruct_states
from experiments.run_match import build_agent
from game.rules import get_legal_actions


MODE_DIR = ROOT / "modes" / "baseline_full"
OUT = ROOT / "final_results" / "baseline_full"
FIGURES = OUT / "figures"
TABLES = OUT / "tables"
AGENT_ORDER = ["random", "rule", "greedy", "minimax", "expectimax", "mcts"]
CARD_ORDER = ["move1", "move2", "mobilize", "capture", "swap"]
COLORS = {
    "random": "#8c8c8c",
    "rule": "#59a14f",
    "greedy": "#4e79a7",
    "minimax": "#f28e2b",
    "expectimax": "#e15759",
    "mcts": "#b07aa1",
}
RNG = np.random.default_rng(20260723)


def ensure_dirs() -> None:
    FIGURES.mkdir(parents=True, exist_ok=True)
    TABLES.mkdir(parents=True, exist_ok=True)


def read_config() -> dict:
    return json.loads((MODE_DIR / "config.json").read_text(encoding="utf-8"))


def load_results() -> pd.DataFrame:
    frames = []
    for path in sorted((MODE_DIR / "results").glob("*.csv")):
        frame = pd.read_csv(path)
        frame["pair"] = path.stem
        frames.append(frame)
    results = pd.concat(frames, ignore_index=True)
    results["game"] = results["game"].astype(int)
    results["score_a"] = results["score_a"].astype(int)
    results["score_b"] = results["score_b"].astype(int)
    results["draw"] = results["winner"].eq("draw")
    return results


def bootstrap_ci(values: np.ndarray, reps: int = 5000) -> tuple[float, float]:
    values = np.asarray(values, dtype=float)
    if len(values) == 0:
        return (math.nan, math.nan)
    samples = RNG.choice(values, size=(reps, len(values)), replace=True).mean(axis=1)
    return tuple(np.quantile(samples, [0.025, 0.975]))


def long_results(results: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for row in results.itertuples(index=False):
        for seat, agent, opponent, score, opp_score in (
            ("first", row.agent_a, row.agent_b, row.score_a, row.score_b),
            ("second", row.agent_b, row.agent_a, row.score_b, row.score_a),
        ):
            player = "A" if seat == "first" else "B"
            outcome = 1.0 if row.winner == player else 0.5 if row.winner == "draw" else 0.0
            rows.append(
                {
                    "pair": row.pair,
                    "game": row.game,
                    "agent": agent,
                    "opponent": opponent,
                    "seat": seat,
                    "score": score,
                    "opponent_score": opp_score,
                    "margin": score - opp_score,
                    "outcome": outcome,
                    "win": outcome == 1,
                    "draw": outcome == 0.5,
                }
            )
    return pd.DataFrame(rows)


def summarize_performance(long: pd.DataFrame) -> pd.DataFrame:
    competitive = long[long.agent != long.opponent]
    rows = []
    for agent in AGENT_ORDER:
        data = competitive[competitive.agent == agent]
        ci_lo, ci_hi = bootstrap_ci(data.outcome.to_numpy())
        margin_lo, margin_hi = bootstrap_ci(data.margin.to_numpy())
        rows.append(
            {
                "agent": agent,
                "games": len(data),
                "wins": int(data.win.sum()),
                "draws": int(data.draw.sum()),
                "losses": int(len(data) - data.win.sum() - data.draw.sum()),
                "win_rate": data.win.mean(),
                "win_points_rate": data.outcome.mean(),
                "win_points_ci_low": ci_lo,
                "win_points_ci_high": ci_hi,
                "mean_score": data.score.mean(),
                "mean_opponent_score": data.opponent_score.mean(),
                "mean_margin": data.margin.mean(),
                "margin_ci_low": margin_lo,
                "margin_ci_high": margin_hi,
            }
        )
    return pd.DataFrame(rows).sort_values(
        ["win_points_rate", "mean_margin"], ascending=False
    )


def summarize_seats(long: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    competitive = long[long.agent != long.opponent]
    rows = []
    for agent in AGENT_ORDER:
        for seat in ("first", "second"):
            data = competitive[(competitive.agent == agent) & (competitive.seat == seat)]
            ci_lo, ci_hi = bootstrap_ci(data.outcome.to_numpy())
            rows.append(
                {
                    "agent": agent,
                    "seat": seat,
                    "games": len(data),
                    "wins": int(data.win.sum()),
                    "draws": int(data.draw.sum()),
                    "losses": int(len(data) - data.win.sum() - data.draw.sum()),
                    "win_rate": data.win.mean(),
                    "win_points_rate": data.outcome.mean(),
                    "win_points_ci_low": ci_lo,
                    "win_points_ci_high": ci_hi,
                    "mean_score": data.score.mean(),
                    "mean_margin": data.margin.mean(),
                }
            )
    seat = pd.DataFrame(rows)

    paired_rows = []
    for agent in AGENT_ORDER:
        first = competitive[
            (competitive.agent == agent) & (competitive.seat == "first")
        ].set_index(["opponent", "game"])
        second = competitive[
            (competitive.agent == agent) & (competitive.seat == "second")
        ].set_index(["opponent", "game"])
        common = first.index.intersection(second.index)
        outcome_diff = first.loc[common, "outcome"].to_numpy() - second.loc[
            common, "outcome"
        ].to_numpy()
        margin_diff = first.loc[common, "margin"].to_numpy() - second.loc[
            common, "margin"
        ].to_numpy()
        out_lo, out_hi = bootstrap_ci(outcome_diff)
        mar_lo, mar_hi = bootstrap_ci(margin_diff)
        paired_rows.append(
            {
                "agent": agent,
                "paired_seeds": len(common),
                "first_minus_second_win_points": outcome_diff.mean(),
                "win_points_diff_ci_low": out_lo,
                "win_points_diff_ci_high": out_hi,
                "first_minus_second_margin": margin_diff.mean(),
                "margin_diff_ci_low": mar_lo,
                "margin_diff_ci_high": mar_hi,
            }
        )
    return seat, pd.DataFrame(paired_rows)


def head_to_head(long: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    competitive = long[long.agent != long.opponent]
    matrix = pd.DataFrame(index=AGENT_ORDER, columns=AGENT_ORDER, dtype=float)
    detail = []
    for agent in AGENT_ORDER:
        for opponent in AGENT_ORDER:
            if agent == opponent:
                matrix.loc[agent, opponent] = np.nan
                continue
            data = competitive[
                (competitive.agent == agent) & (competitive.opponent == opponent)
            ]
            matrix.loc[agent, opponent] = data.outcome.mean()
            detail.append(
                {
                    "agent": agent,
                    "opponent": opponent,
                    "games": len(data),
                    "wins": int(data.win.sum()),
                    "draws": int(data.draw.sum()),
                    "losses": int(len(data) - data.win.sum() - data.draw.sum()),
                    "win_points_rate": data.outcome.mean(),
                    "mean_margin": data.margin.mean(),
                }
            )
    return matrix, pd.DataFrame(detail)


def parse_game_logs(config: dict, results: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    event_rows = []
    game_rows = []
    trajectory_rows = []
    capture_score = int(config["rules"]["capture_score"])
    result_lookup = {
        (r.agent_a, r.agent_b, int(r.game)): (int(r.score_a), int(r.score_b))
        for r in results.itertuples(index=False)
    }

    for game_dir in sorted((MODE_DIR / "games").iterdir()):
        if not game_dir.is_dir():
            continue
        agent_a, agent_b = game_dir.name.split("_", 1)
        for path in sorted(game_dir.glob("*.csv"), key=lambda p: int(p.stem)):
            game_id = int(path.stem)
            with path.open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            events = []
            personal_turn = {"A": 0, "B": 0}
            action_counts = {"A": Counter(), "B": Counter()}
            passes = {"A": 0, "B": 0}
            captures = {"A": 0, "B": 0}
            net_captures = {"A": 0, "B": 0}
            exposure = {"A": Counter(), "B": Counter()}

            for idx in range(1, len(rows)):
                before, after = rows[idx - 1], rows[idx]
                actor = "A" if int(before["player"]) == 0 else "B"
                agent = agent_a if actor == "A" else agent_b
                opponent = agent_b if actor == "A" else agent_a
                personal_turn[actor] += 1
                for card in set(before[f"card_{i}"] for i in range(3)):
                    exposure[actor][card] += 1
                action_index = int(after["action"])
                is_pass = action_index < 0
                card = "pass" if is_pass else before[f"card_{action_index}"]
                if is_pass:
                    passes[actor] += 1
                else:
                    action_counts[actor][card] += 1
                is_capture = card == "capture"
                is_net = is_capture and after["src_1"] not in {"-1", "None", ""}
                captures[actor] += int(is_capture)
                net_captures[actor] += int(is_net)
                score_before = int(before["score_a" if actor == "A" else "score_b"])
                score_after = int(after["score_a" if actor == "A" else "score_b"])
                event = {
                    "agent_a": agent_a,
                    "agent_b": agent_b,
                    "game": game_id,
                    "event_index": idx,
                    "personal_turn": personal_turn[actor],
                    "player": actor,
                    "seat": "first" if actor == "A" else "second",
                    "agent": agent,
                    "opponent": opponent,
                    "card": card,
                    "pass": is_pass,
                    "capture": is_capture,
                    "net_capture": is_net,
                    "score_increment": score_after - score_before,
                    "score_after": score_after,
                }
                event_rows.append(event)
                events.append(event)
                trajectory_rows.append(
                    {
                        "agent": agent,
                        "opponent": opponent,
                        "seat": event["seat"],
                        "game": game_id,
                        "personal_turn": personal_turn[actor],
                        "score": score_after,
                    }
                )

            expected = result_lookup[(agent_a, agent_b, game_id)]
            final_logged = (int(rows[-1]["score_a"]), int(rows[-1]["score_b"]))
            if expected != final_logged:
                raise ValueError(f"Score mismatch in {path}: {final_logged} != {expected}")
            final_pass_streak = 0
            for event in reversed(events):
                if not event["pass"]:
                    break
                final_pass_streak += 1
            for actor, agent, opponent, score in (
                ("A", agent_a, agent_b, expected[0]),
                ("B", agent_b, agent_a, expected[1]),
            ):
                capture_points = capture_score * captures[actor]
                game_rows.append(
                    {
                        "agent_a": agent_a,
                        "agent_b": agent_b,
                        "game": game_id,
                        "agent": agent,
                        "opponent": opponent,
                        "seat": "first" if actor == "A" else "second",
                        "score": score,
                        "captures": captures[actor],
                        "net_captures": net_captures[actor],
                        "capture_points": capture_points,
                        "control_points": score - capture_points,
                        "passes": passes[actor],
                        "pass_rate": passes[actor] / max(personal_turn[actor], 1),
                        **{f"chosen_{card}": action_counts[actor][card] for card in CARD_ORDER},
                        **{f"exposed_{card}": exposure[actor][card] for card in CARD_ORDER},
                        "game_final_pass_streak": final_pass_streak,
                        "game_deadlocked": final_pass_streak >= 10,
                    }
                )
    return pd.DataFrame(event_rows), pd.DataFrame(game_rows), pd.DataFrame(trajectory_rows)


def strategy_tables(events: pd.DataFrame, games: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    action_rows = []
    non_pass = events[~events["pass"]]
    for agent in AGENT_ORDER:
        agent_events = events[events.agent == agent]
        selected = non_pass[non_pass.agent == agent]
        game_data = games[games.agent == agent]
        for card in CARD_ORDER:
            chosen = int((selected.card == card).sum())
            exposure = int(game_data[f"exposed_{card}"].sum())
            action_rows.append(
                {
                    "agent": agent,
                    "card": card,
                    "chosen": chosen,
                    "share_of_non_pass_actions": chosen / max(len(selected), 1),
                    "market_exposure_turns": exposure,
                    "chosen_per_exposure_turn": chosen / max(exposure, 1),
                }
            )
        # Pass is deliberately a separate row; it is not a strategic card choice.
        action_rows.append(
            {
                "agent": agent,
                "card": "pass",
                "chosen": int(agent_events["pass"].sum()),
                "share_of_non_pass_actions": np.nan,
                "market_exposure_turns": np.nan,
                "chosen_per_exposure_turn": np.nan,
            }
        )
    action = pd.DataFrame(action_rows)

    strategy_rows = []
    for agent in AGENT_ORDER:
        data = games[games.agent == agent]
        cap = data.captures.sum()
        strategy_rows.append(
            {
                "agent": agent,
                "agent_games_including_self_play": len(data),
                "mean_score": data.score.mean(),
                "mean_captures": data.captures.mean(),
                "net_share_of_captures": data.net_captures.sum() / max(cap, 1),
                "mean_capture_points": data.capture_points.mean(),
                "mean_control_points": data.control_points.mean(),
                "control_share_of_points": data.control_points.sum() / max(data.score.sum(), 1),
                "mean_pass_rate": data.pass_rate.mean(),
                "deadlocked_game_exposure_rate": data.game_deadlocked.mean(),
            }
        )
    return action, pd.DataFrame(strategy_rows)


def score_trajectories(trajectories: pd.DataFrame) -> pd.DataFrame:
    return (
        trajectories.groupby(["agent", "personal_turn"], as_index=False)
        .agg(mean_score=("score", "mean"), std_score=("score", "std"), observations=("score", "size"))
    )


def select_benchmark_states(mode: dict) -> list[tuple[str, int, int, object]]:
    selected = []
    sources = [("expectimax", "random", 0), ("expectimax", "random", 7)]
    for agent_a, agent_b, game_id in sources:
        states = reconstruct_states(mode, agent_a, agent_b, game_id, validate=True)
        for target in (15, 50, 85):
            candidates = [
                (abs(i - target), i, state)
                for i, state in enumerate(states[:-1])
                if len(get_legal_actions(state)) >= 5
            ]
            _, index, state = min(candidates, key=lambda item: (item[0], item[1]))
            selected.append((f"{agent_a}_{agent_b}", game_id, index, state))
    return selected


def runtime_benchmark(config: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    mode = load_mode("baseline_full")
    states = select_benchmark_states(mode)
    params_by_agent = {entry["name"]: entry["params"] for entry in config["agents"]}
    repetitions = {
        "random": 200,
        "rule": 10,
        "greedy": 5,
        "minimax": 2,
        "expectimax": 1,
        "mcts": 1,
    }
    raw = []
    for state_number, (pair, game_id, state_index, state) in enumerate(states):
        legal = get_legal_actions(state)
        for agent_name in AGENT_ORDER:
            params = dict(params_by_agent[agent_name])
            if params.get("seed", "not-present") is None:
                params["seed"] = 1000 + state_number
            agent = build_agent(agent_name, params)
            reps = repetitions[agent_name]
            started = time.perf_counter()
            for _ in range(reps):
                agent.choose_action(state, legal)
            elapsed_ms = (time.perf_counter() - started) * 1000 / reps
            raw.append(
                {
                    "agent": agent_name,
                    "source_pair": pair,
                    "source_game": game_id,
                    "source_state_index": state_index,
                    "legal_actions": len(legal),
                    "repetitions": reps,
                    "milliseconds_per_decision": elapsed_ms,
                    "last_nodes": getattr(agent, "last_nodes", np.nan),
                }
            )
    raw_df = pd.DataFrame(raw)
    summary = (
        raw_df.groupby("agent", as_index=False)
        .agg(
            states=("milliseconds_per_decision", "size"),
            median_ms=("milliseconds_per_decision", "median"),
            mean_ms=("milliseconds_per_decision", "mean"),
            min_ms=("milliseconds_per_decision", "min"),
            max_ms=("milliseconds_per_decision", "max"),
            median_nodes=("last_nodes", "median"),
        )
    )
    return summary, raw_df


def save_tables(
    performance: pd.DataFrame,
    seats: pd.DataFrame,
    paired_seats: pd.DataFrame,
    h2h: pd.DataFrame,
    h2h_detail: pd.DataFrame,
    runtime: pd.DataFrame,
    runtime_raw: pd.DataFrame,
    action: pd.DataFrame,
    strategy: pd.DataFrame,
    trajectories: pd.DataFrame,
    games: pd.DataFrame,
) -> None:
    performance.to_csv(TABLES / "01_agent_performance.csv", index=False, float_format="%.6f")
    seats.to_csv(TABLES / "02_seat_performance.csv", index=False, float_format="%.6f")
    paired_seats.to_csv(TABLES / "03_paired_seat_effects.csv", index=False, float_format="%.6f")
    h2h.to_csv(TABLES / "04_head_to_head_win_points.csv", float_format="%.6f")
    h2h_detail.to_csv(TABLES / "05_matchup_detail.csv", index=False, float_format="%.6f")
    runtime.to_csv(TABLES / "06_runtime_benchmark.csv", index=False, float_format="%.6f")
    runtime_raw.to_csv(TABLES / "07_runtime_benchmark_raw.csv", index=False, float_format="%.6f")
    action.to_csv(TABLES / "08_action_profiles.csv", index=False, float_format="%.6f")
    strategy.to_csv(TABLES / "09_strategy_metrics.csv", index=False, float_format="%.6f")
    trajectories.to_csv(TABLES / "10_score_trajectories.csv", index=False, float_format="%.6f")
    games.to_csv(TABLES / "11_game_level_strategy.csv", index=False, float_format="%.6f")


def style_axis(ax, title: str, ylabel: str = "", xlabel: str = "") -> None:
    ax.set_title(title, loc="left", fontsize=12, fontweight="bold")
    ax.set_ylabel(ylabel)
    ax.set_xlabel(xlabel)
    ax.grid(axis="y", alpha=0.25)
    ax.spines[["top", "right"]].set_visible(False)


def plot_performance(performance: pd.DataFrame) -> None:
    data = performance.sort_values("win_points_rate")
    fig, axes = plt.subplots(1, 2, figsize=(11, 5))
    colors = [COLORS[a] for a in data.agent]
    xerr = np.vstack(
        [
            data.win_points_rate - data.win_points_ci_low,
            data.win_points_ci_high - data.win_points_rate,
        ]
    )
    axes[0].barh(data.agent, data.win_points_rate * 100, color=colors)
    axes[0].errorbar(
        data.win_points_rate * 100,
        data.agent,
        xerr=xerr * 100,
        fmt="none",
        ecolor="black",
        capsize=3,
    )
    axes[0].axvline(50, color="black", linewidth=1, linestyle="--")
    style_axis(axes[0], "Competitive outcome", "Agent", "Win points (%)")
    axes[1].barh(data.agent, data.mean_margin, color=colors)
    axes[1].axvline(0, color="black", linewidth=1)
    style_axis(axes[1], "Score margin", "", "Mean own − opponent score")
    fig.suptitle("Overall performance (self-play excluded; 300 games per agent)", fontsize=14)
    fig.tight_layout()
    fig.savefig(FIGURES / "01_overall_performance.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def plot_seats(seats: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(10, 5.5))
    x = np.arange(len(AGENT_ORDER))
    width = 0.36
    for offset, seat, color in ((-width / 2, "first", "#4e79a7"), (width / 2, "second", "#f28e2b")):
        data = seats[seats.seat == seat].set_index("agent").loc[AGENT_ORDER]
        ax.bar(x + offset, data.win_points_rate * 100, width, label=seat.title(), color=color)
    ax.axhline(50, color="black", linestyle="--", linewidth=1)
    ax.set_xticks(x, AGENT_ORDER)
    ax.legend(frameon=False)
    style_axis(ax, "Performance by move order (self-play excluded)", "", "Win points (%)")
    fig.tight_layout()
    fig.savefig(FIGURES / "02_first_vs_second.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def plot_h2h(h2h: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(7.5, 6.5))
    values = h2h.loc[AGENT_ORDER, AGENT_ORDER].to_numpy(dtype=float) * 100
    image = ax.imshow(values, cmap="RdYlGn", vmin=0, vmax=100)
    for i in range(len(AGENT_ORDER)):
        for j in range(len(AGENT_ORDER)):
            if i != j:
                ax.text(j, i, f"{values[i, j]:.0f}", ha="center", va="center", fontsize=9)
    ax.set_xticks(range(len(AGENT_ORDER)), AGENT_ORDER, rotation=35, ha="right")
    ax.set_yticks(range(len(AGENT_ORDER)), AGENT_ORDER)
    ax.set_xlabel("Opponent")
    ax.set_ylabel("Agent")
    ax.set_title("Head-to-head win points (%)\n60 games per off-diagonal cell, both move orders", loc="left")
    fig.colorbar(image, ax=ax, label="Win points (%)", shrink=0.8)
    fig.tight_layout()
    fig.savefig(FIGURES / "03_head_to_head.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def plot_runtime(performance: pd.DataFrame, runtime: pd.DataFrame) -> None:
    merged = performance.merge(runtime, on="agent")
    fig, ax = plt.subplots(figsize=(8, 5.5))
    for row in merged.itertuples(index=False):
        ax.scatter(
            row.median_ms,
            row.win_points_rate * 100,
            s=100,
            color=COLORS[row.agent],
            edgecolor="white",
            linewidth=0.8,
        )
        ax.annotate(row.agent, (row.median_ms, row.win_points_rate * 100), xytext=(5, 5), textcoords="offset points")
    ax.set_xscale("log")
    ax.axhline(50, color="black", linestyle="--", linewidth=1)
    style_axis(
        ax,
        "Performance–cost trade-off",
        "Competitive win points (%)",
        "Median decision time (ms, log scale)",
    )
    fig.tight_layout()
    fig.savefig(FIGURES / "04_runtime_vs_performance.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def plot_actions(action: pd.DataFrame) -> None:
    pivot = (
        action[action.card.isin(CARD_ORDER)]
        .pivot(index="agent", columns="card", values="share_of_non_pass_actions")
        .loc[AGENT_ORDER, CARD_ORDER]
    )
    fig, ax = plt.subplots(figsize=(10, 5.5))
    bottom = np.zeros(len(pivot))
    palette = ["#4e79a7", "#76b7b2", "#59a14f", "#e15759", "#b07aa1"]
    for card, color in zip(CARD_ORDER, palette):
        values = pivot[card].to_numpy() * 100
        ax.bar(pivot.index, values, bottom=bottom, label=card, color=color)
        bottom += values
    ax.legend(ncol=5, frameon=False, loc="upper center", bbox_to_anchor=(0.5, 1.12))
    style_axis(ax, "Action profile (non-pass turns)", "", "Share of selected cards (%)")
    fig.tight_layout()
    fig.savefig(FIGURES / "05_action_profiles.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def plot_scoring(strategy: pd.DataFrame) -> None:
    data = strategy.set_index("agent").loc[AGENT_ORDER]
    fig, ax = plt.subplots(figsize=(9, 5.5))
    ax.bar(data.index, data.mean_capture_points, label="Capture points", color="#e15759")
    ax.bar(
        data.index,
        data.mean_control_points,
        bottom=data.mean_capture_points,
        label="Scoring-cell control points",
        color="#59a14f",
    )
    ax.legend(frameon=False)
    style_axis(ax, "How agents score (all games, including self-play)", "", "Mean points per game")
    fig.tight_layout()
    fig.savefig(FIGURES / "06_scoring_sources.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def plot_trajectories(trajectories: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(9, 5.5))
    for agent in AGENT_ORDER:
        data = trajectories[trajectories.agent == agent]
        ax.plot(data.personal_turn, data.mean_score, label=agent, color=COLORS[agent], linewidth=2)
    ax.legend(frameon=False, ncol=3)
    style_axis(ax, "Mean score accumulation", "Mean score", "Personal turn")
    fig.tight_layout()
    fig.savefig(FIGURES / "07_score_trajectories.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def plot_deadlocks(strategy: pd.DataFrame) -> None:
    data = strategy.set_index("agent").loc[AGENT_ORDER]
    fig, axes = plt.subplots(1, 2, figsize=(11, 5))
    colors = [COLORS[a] for a in AGENT_ORDER]
    axes[0].bar(AGENT_ORDER, data.mean_pass_rate * 100, color=colors)
    style_axis(axes[0], "Pass turns", "", "Mean share of turns (%)")
    axes[0].tick_params(axis="x", rotation=35)
    axes[1].bar(AGENT_ORDER, data.deadlocked_game_exposure_rate * 100, color=colors)
    style_axis(axes[1], "Games ending in ≥10 consecutive passes", "", "Agent-game exposure (%)")
    axes[1].tick_params(axis="x", rotation=35)
    fig.suptitle("Absorbing-market deadlocks in the recorded baseline", fontsize=14)
    fig.tight_layout()
    fig.savefig(FIGURES / "08_passes_and_deadlocks.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def fmt_pct(value: float) -> str:
    return f"{100 * value:.1f}%"


def write_analysis(
    config: dict,
    results: pd.DataFrame,
    performance: pd.DataFrame,
    seats: pd.DataFrame,
    paired_seats: pd.DataFrame,
    runtime: pd.DataFrame,
    strategy: pd.DataFrame,
    games: pd.DataFrame,
) -> None:
    rank = performance.reset_index(drop=True)
    best = rank.iloc[0]
    second = rank.iloc[1]
    seat_a = seats[seats.seat == "first"].set_index("agent")
    seat_b = seats[seats.seat == "second"].set_index("agent")
    overall_nonself = results[results.agent_a != results.agent_b]
    a_win_points = (
        (overall_nonself.winner == "A").astype(float)
        + 0.5 * (overall_nonself.winner == "draw").astype(float)
    ).mean()
    deadlocked_games = (
        games[["agent_a", "agent_b", "game", "game_deadlocked"]]
        .drop_duplicates()
        .game_deadlocked
    )
    deadlock_rate = deadlocked_games.mean()
    pass_rate = games.passes.sum() / (len(results) * config["rules"]["turns_per_player"] * 2)
    slow = runtime.sort_values("median_ms", ascending=False).iloc[0]
    fast_search = runtime[runtime.agent.isin(["greedy", "minimax", "expectimax", "mcts"])].sort_values("median_ms").iloc[0]
    strategic = strategy.set_index("agent")
    top_control = strategic.mean_control_points.idxmax()
    top_capture = strategic.mean_captures.idxmax()

    text = f"""# Baseline Full: analysis and interpretation

## Executive summary

This package analyzes all **{len(results):,} games** in `modes/baseline_full`: 36 ordered pairings, 30 seeded games per pairing, with 100 scheduled turns per game. Competitive rankings exclude self-play, leaving 300 observations per agent (150 first-player and 150 second-player games). Draws count as half a win in the main “win points” measure.

The strongest aggregate performer is **{best.agent}** with {fmt_pct(best.win_points_rate)} win points and a mean score margin of {best.mean_margin:.2f}; **{second.agent}** is next at {fmt_pct(second.win_points_rate)}. These estimates describe this board, deck, heuristic, and parameter budget—not universal agent strength.

Move order matters: across all non-self matchups, Player A receives {fmt_pct(a_win_points)} of win points. Agent-specific first/second results are in Figure 02 and the paired-seed differences in Table 03. Pairing the same agent/opponent/seed across reversed orientations is the cleanest available estimate because it controls the shuffled deck seed.

A major experimental finding is the frequency of **absorbing market deadlocks**. In {fmt_pct(deadlock_rate)} of games, the final 10 or more scheduled turns are all passes; {fmt_pct(pass_rate)} of all scheduled turns are passes. The rules leave the market unchanged on a pass, so a market containing only currently illegal cards can remain stuck forever. This is not merely cosmetic: it truncates strategic interaction and can preserve an early lead. Report this prominently and test a pass/redraw rule as a robustness condition.

## 1. What the project studies

Graph Card Control is a two-player, alternating, perfect-information strategy game with stochastic card refills. Each player controls three pieces on a 5×5 grid. The default match lasts 50 turns per player. Captures score 3 points, while occupying the center scoring cell yields 1 point after every own turn. Players choose from a shared three-card market containing movement, mobilization, capture, and swap actions. The only hidden uncertainty is the next card drawn; the remaining card-type distribution is known.

The experiment compares two baselines (`random`, `rule`) with four evaluation/search agents (`greedy`, depth-2 `minimax`, depth-2 `expectimax`, and `mcts` with 200 simulations and rollout depth 20). The current minimax implementation does **not** create chance nodes: its ordinary transition call consumes the next concrete card from the shuffled deck stored in `GameState`, so its search follows the realized hidden deck order deterministically. Expectimax instead enumerates possible replacement card types and probability-weights their successor values; MCTS estimates longer-run values through sampled simulations.

## 2. Performance and move order

Figure 01 gives both win points and score margin. Figure 03 is essential context: aggregate rankings can hide rock–paper–scissors matchup structure. Each off-diagonal head-to-head cell pools 30 games in each orientation (60 total).

The first/second comparison should be interpreted in two layers:

1. **Overall game bias:** Player A obtains {fmt_pct(a_win_points)} of competitive win points.
2. **Agent sensitivity:** compare each agent’s {', '.join(f'{a}: {fmt_pct(seat_a.loc[a, "win_points_rate"])} first vs {fmt_pct(seat_b.loc[a, "win_points_rate"])} second' for a in AGENT_ORDER)}.

Table 03 reports paired first-minus-second differences over identical opponent/seed combinations, including bootstrap 95% intervals. A confidence interval spanning zero means the current 30-seed-per-orientation sample does not clearly establish a seat effect for that agent.

## 3. Runtime versus playing strength

The original CSV files do **not** record elapsed time. Figure 04 therefore uses a post-hoc benchmark: every agent chooses an action from the same six reconstructed early/middle/late recorded states. Values are median wall-clock milliseconds per decision on this machine, not whole-match runtimes. Fast agents are repeated within each state to reduce timer noise; search-heavy agents run fewer repetitions.

The slowest median decision time is **{slow.agent}** at {slow.median_ms:.3f} ms. Among heuristic/search agents, the cheapest measured option is **{fast_search.agent}** at {fast_search.median_ms:.3f} ms. The performance–cost plot supports an explicit efficiency argument: prefer an agent on the upper-left frontier, and describe any extra win rate in terms of its multiplicative runtime cost. Do not mix these post-hoc timings with the original outcome sample as if they were collected simultaneously.

## 4. Dominant strategies

“Strategy” is operationalized using three observable quantities:

- selected card type on non-pass turns (Figure 05);
- scoring source—3 points per logged capture versus residual scoring-cell control points (Figure 06);
- capture style—melee versus net launcher, identified by the second launcher source field (Table 09).

**{top_control}** earns the most scoring-cell control points ({strategic.loc[top_control, 'mean_control_points']:.2f} per game), while **{top_capture}** makes the most captures ({strategic.loc[top_capture, 'mean_captures']:.2f} per game). The contrast between `rule` and `greedy` is particularly informative: they average {strategic.loc['rule', 'mean_captures']:.2f} and {strategic.loc['greedy', 'mean_captures']:.2f} captures, respectively, but `rule` earns {strategic.loc['rule', 'mean_control_points']:.2f} control points versus only {strategic.loc['greedy', 'mean_control_points']:.2f} for `greedy`. The dominant pattern is therefore not capture volume alone; it is opportunistic capture combined with persistent scoring-cell control.

These are behavioral signatures, not causal effects: card availability, legality, opponent behavior, and deadlocks all constrain what an agent can choose. Table 08 therefore includes a descriptive `chosen_per_exposure_turn` measure alongside raw choice share; exposure means the card appeared in the market, not that at least one action using it was legal.

Figure 07 shows when scores accumulate. Plateaus near the end of a match should be read together with Figure 08: many are caused by pass streaks, not stable defensive equilibrium.

## 5. Threats to validity

- **One environment:** the ranking is conditional on the default symmetric 5×5 board, one 1-point center, three pieces each, and the default 28-card deck.
- **One heuristic:** greedy, minimax, expectimax, and MCTS rollouts share the same evaluation weights, so their errors are correlated.
- **Minimax has hidden-order information:** minimax calls `apply_action` without a forced draw, causing search to use the next concrete card in the state’s shuffled deck. Under the written rules only deck composition—not order—is public. Its strong result may therefore be inflated by oracle-like future-card information and should be rerun after correcting the chance model.
- **Budget mismatch:** depth 2, top-k 10, and 200 MCTS simulations are not guaranteed to represent equal computation.
- **Seed dependence:** 30 seeds per orientation is useful but still finite. Reversed orientations reuse seeds, which is good for paired seat analysis but means observations are not all independent.
- **Deadlocks:** end-of-game pass streaks reduce the effective horizon and may reward early scoring disproportionately.
- **Timing provenance:** runtime is post-hoc and machine-specific because it was absent from the original logs.

## 6. Recommended follow-up experiments

Use a factorial design where one factor changes at a time from the baseline, retain mirrored orientations, and increase to at least 50–100 seeds for close comparisons. Record per-decision elapsed time, expanded nodes/simulations, pass status, and terminal deadlock length directly during the run.

1. **Boards:** test the existing `crossfire` board plus small/large and multi-scoring-cell layouts. Hypothesis: longer distances favor deeper planning; multiple weighted cells reduce center congestion and may reduce deadlocks.
2. **Pieces per player:** compare 2, 3, and 4 pieces on boards sized to avoid spawn congestion. Hypothesis: more pieces increase branching, net opportunities, blocking, and MCTS’s sampling burden.
3. **Deck composition:** create movement-heavy, capture-heavy, swap-heavy, and balanced decks while keeping deck size fixed. Include a robustness variant that redraws or refreshes the market after a pass. Hypothesis: capture-heavy markets increase absorbing illegal-card states under the current rule.
4. **Win condition / scoring:** the implemented game uses a fixed horizon and highest score, not a point threshold. Test horizons (25/50/75 turns per player), capture values (1/3/5), scoring-cell weights, and—only as a separate rule variant—first-to-target thresholds. Threshold games confound performance with variable runtime, so analyze both win rate and turns-to-finish.
5. **Expectimax depth:** depths 1, 2, and 3 (possibly 4 if feasible), holding `top_k=10`, with time/node budgets recorded.
6. **MCTS budget:** a grid over simulations {{50, 100, 200, 500, 1000}} and rollout depths {{5, 10, 20, 40}}. Plot win points against wall time to find diminishing returns.
7. **Fair-budget comparison:** cap all search agents by equal milliseconds per move in addition to parameter sweeps. This answers whether an algorithm is better, not merely allowed more computation.
8. **Ablations:** remove heuristic terms one at a time, especially scoring-cell distance, capture threat, and net potential, to explain which knowledge drives performance.

For each follow-up, pre-register the primary metric (competitive win points), secondary metrics (score margin, control/capture scoring split, deadlocks), and the paired-seed seat contrast. Avoid selecting only favorable configurations after seeing results.

## 7. Reproducibility

Run:

```powershell
python analysis/baseline_full_report.py
```

The script reads raw data without modifying it, validates each log’s final score against its result CSV, regenerates all tables/figures, uses a fixed bootstrap seed, and rewrites this analysis and the index. The mode snapshot records code version `{config.get("code_version", "unknown")}` and seeds 0–29.
"""
    (OUT / "01_ANALYSIS.md").write_text(text, encoding="utf-8")


def write_follow_up_plan() -> None:
    text = """# Follow-up experiment plan

## Purpose

The baseline establishes a ranking on one configuration, but it also exposes a pass-deadlock mechanism and a large compute-budget imbalance. The next phase should test robustness before making broad claims about algorithm quality.

## Recommended execution order

| Priority | Experiment | Values | Main question | Primary plots |
|---:|---|---|---|---|
| 1 | Chance-model correction | realized hidden order; adversarial draw; probability-weighted draw | How much of minimax's strength comes from seeing the concrete future deck? | win points, score margin, nodes/time |
| 2 | Pass-rule robustness | unchanged market (baseline); discard/redraw one card; refresh all three cards | Are rankings driven by absorbing illegal markets? | win points, deadlock rate, effective turns |
| 3 | Existing board | `default`; `crossfire` | Does a larger board with two unequal scoring cells change the ranking? | matchup matrix, scoring-source split |
| 4 | Equal compute | fixed per-move time budgets | Does search still help when computation is controlled? | win points vs time |
| 5 | Expectimax depth | 1, 2, 3; depth 4 only if feasible | Does exact chance expansion repay its exponential cost? | win points, ms/move, nodes/move |
| 6 | MCTS grid | simulations 50, 100, 200, 500, 1000 × rollout depth 5, 10, 20, 40 | Where are the diminishing returns? | heatmaps for strength and time |
| 7 | Deck mix | movement-heavy; balanced; capture-heavy; swap-heavy | Which action supply favors each planning method? | action profile, deadlocks, ranking |
| 8 | Piece count | 2, 3, 4 per player on compatible boards | How does branching and congestion affect agents? | strength/time Pareto frontier |
| 9 | Scoring/horizon | capture score 1, 3, 5; 25, 50, 75 turns/player | Is the ranking stable under strategic incentives and horizon? | win points, score source, trajectories |

## Minimal confirmatory design

- Run every ordered non-self pair in both orientations.
- Use the same 100 game seeds per orientation for every configuration.
- Treat seed as a paired/blocking variable when comparing configurations or move order.
- Keep the baseline configuration unchanged as a control in every batch.
- Record wall-clock decision time and search nodes/simulations per turn.
- Record legal-action count, pass events, final pass streak, selected card, capture mode, and score increment.
- Report win points (win=1, draw=0.5), score margin, and deadlock rate as co-primary practical outcomes.
- Use confidence intervals and effect sizes; do not rely only on null-hypothesis tests.

With six agents, a full ordered round-robin has 30 non-self ordered pairs. At 100 seeds, that is 3,000 games per configuration. Parameter sweeps can become expensive quickly, so first screen configurations with 20 seeds and then rerun only predeclared promising settings with 100 seeds. Do not use the screening games again as confirmatory evidence.

## Configuration notes

### Boards and piece counts

`boards/crossfire.json` already provides a 5×7 board with 1-point and 2-point scoring cells plus a blocked center segment. Piece count is encoded by the number of spawn positions in a board JSON file, so 2-piece and 4-piece tests require new board definitions with matching A/B spawn lists. Keep boards symmetric unless asymmetry is the factor being studied.

### Deck composition

Keep total deck size at 28 for the first comparison so only proportions change. Suggested compositions:

| Deck | move1 | move2 | mobilize | capture | swap |
|---|---:|---:|---:|---:|---:|
| balanced baseline | 8 | 6 | 5 | 5 | 4 |
| movement-heavy | 10 | 8 | 6 | 2 | 2 |
| capture-heavy | 5 | 4 | 4 | 11 | 4 |
| swap-heavy | 6 | 5 | 4 | 4 | 9 |

The capture-heavy condition must be paired with the pass-rule robustness test: otherwise increased deadlocks may be mistaken for strategic behavior.

### Point requirements and win conditions

The current engine ends after a fixed number of turns and awards the win to the higher score. `--turns` and `--capture-score` are already configurable. A “first to N points” condition is not currently a mode parameter; it is a different termination rule and requires an engine/config change plus tests. Treat it as a separate ruleset, and report turns-to-finish alongside win rate because match duration becomes endogenous.

### Search budgets

Use the existing mode parameter interface for expectimax and MCTS, for example:

```powershell
python src/experiments/create_mode.py expectimax_d3 --agents expectimax rule --num-games 100 --param expectimax.depth=3
python src/experiments/create_mode.py mcts_s500_r20 --agents mcts rule --num-games 100 --param mcts.simulations=500 --param mcts.rollout_depth=20
```

Before launching a large sweep, time one complete game at the largest setting. Expectimax cost can grow sharply with depth because it expands both action and chance branches.

## Analysis model for the final report

For win/loss/draw outcomes, use a paired seed analysis or a mixed-effects/clustered model with agent, seat, configuration, and their interactions; cluster on seed and matchup. For score margin and runtime, show medians as well as means because both may be skewed. The central report claim should be an interaction claim—whether an agent remains strong across boards, decks, and budgets—not just a single baseline ranking.
"""
    (OUT / "02_FOLLOW_UP_EXPERIMENTS.md").write_text(text, encoding="utf-8")


def write_index(performance: pd.DataFrame, runtime: pd.DataFrame) -> None:
    files = [
        ("01_ANALYSIS.md", "Main report-ready interpretation, limitations, and follow-up design"),
        ("02_FOLLOW_UP_EXPERIMENTS.md", "Prioritized experiment matrix and confirmatory design"),
        ("figures/01_overall_performance.png", "Competitive win points and mean score margin"),
        ("figures/02_first_vs_second.png", "Agent performance split by move order"),
        ("figures/03_head_to_head.png", "Combined-orientation matchup matrix"),
        ("figures/04_runtime_vs_performance.png", "Post-hoc decision-time/performance trade-off"),
        ("figures/05_action_profiles.png", "Selected card distribution on non-pass turns"),
        ("figures/06_scoring_sources.png", "Capture versus scoring-cell control points"),
        ("figures/07_score_trajectories.png", "Mean cumulative score by personal turn"),
        ("figures/08_passes_and_deadlocks.png", "Pass frequency and absorbing-market deadlocks"),
        ("tables/01_agent_performance.csv", "Overall competitive ranking with bootstrap intervals"),
        ("tables/02_seat_performance.csv", "First/second descriptive statistics"),
        ("tables/03_paired_seat_effects.csv", "Paired-seed first-minus-second estimates"),
        ("tables/04_head_to_head_win_points.csv", "Head-to-head matrix values"),
        ("tables/05_matchup_detail.csv", "Wins, draws, losses, and margins for every matchup"),
        ("tables/06_runtime_benchmark.csv", "Runtime benchmark summary"),
        ("tables/07_runtime_benchmark_raw.csv", "Per-state runtime measurements and node counts"),
        ("tables/08_action_profiles.csv", "Action choices and market-exposure normalization"),
        ("tables/09_strategy_metrics.csv", "Scoring sources, captures, net use, passes, deadlocks"),
        ("tables/10_score_trajectories.csv", "Plot-ready score trajectory values"),
        ("tables/11_game_level_strategy.csv", "Agent-game strategy observations"),
        ("../../analysis/baseline_full_report.py", "Reproduction script"),
    ]
    ranking_lines = []
    for position, row in enumerate(performance.itertuples(index=False), 1):
        timing = runtime[runtime.agent == row.agent].iloc[0]
        timing_text = f"{timing.median_ms:.4f}" if timing.median_ms < 0.01 else f"{timing.median_ms:.3f}"
        ranking_lines.append(
            f"{position}. **{row.agent}** — {fmt_pct(row.win_points_rate)} win points, "
            f"{row.mean_margin:+.2f} mean margin, {timing_text} ms median benchmark decision"
        )
    file_lines = [f"- [{path}]({path}) — {description}" for path, description in files]
    text = f"""# Baseline Full final-results index

This folder is the report-ready output for `modes/baseline_full`. Files are numbered in recommended reading order. Start with [01_ANALYSIS.md](01_ANALYSIS.md).

## At-a-glance ranking

{chr(10).join(ranking_lines)}

## Files

{chr(10).join(file_lines)}

## Metric conventions

- Self-play is excluded from competitive performance and seat comparisons.
- A win is 1 win point, a draw 0.5, and a loss 0.
- Head-to-head cells combine both orientations and contain 60 games.
- Error intervals are game-level percentile bootstrap 95% intervals with a fixed seed.
- Runtime is a post-hoc same-state benchmark because the original experiment did not log time.
- A game is flagged as deadlocked when its final 10 or more scheduled turns are passes.
"""
    (OUT / "00_INDEX.md").write_text(text, encoding="utf-8")


def main() -> None:
    ensure_dirs()
    config = read_config()
    results = load_results()
    expected = len(config["agents"]) ** 2 * int(config["num_games"])
    if len(results) != expected:
        raise ValueError(f"Expected {expected} result rows, found {len(results)}")
    long = long_results(results)
    performance = summarize_performance(long)
    seats, paired_seats = summarize_seats(long)
    h2h, h2h_detail = head_to_head(long)
    events, games, trajectory_events = parse_game_logs(config, results)
    action, strategy = strategy_tables(events, games)
    trajectories = score_trajectories(trajectory_events)
    runtime, runtime_raw = runtime_benchmark(config)
    save_tables(
        performance,
        seats,
        paired_seats,
        h2h,
        h2h_detail,
        runtime,
        runtime_raw,
        action,
        strategy,
        trajectories,
        games,
    )
    plot_performance(performance)
    plot_seats(seats)
    plot_h2h(h2h)
    plot_runtime(performance, runtime)
    plot_actions(action)
    plot_scoring(strategy)
    plot_trajectories(trajectories)
    plot_deadlocks(strategy)
    write_analysis(config, results, performance, seats, paired_seats, runtime, strategy, games)
    write_follow_up_plan()
    write_index(performance, runtime)
    print(f"Wrote analysis package to {OUT}")
    print(performance[["agent", "win_points_rate", "mean_margin"]].to_string(index=False))


if __name__ == "__main__":
    main()
