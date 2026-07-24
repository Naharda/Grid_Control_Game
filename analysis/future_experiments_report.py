"""Analyze the exploratory future-experiment screening modes.

Run from the repository root:

    python analysis/future_experiments_report.py
"""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "final_results" / "future_experiments"
FIGURES = OUT / "figures"
TABLES = OUT / "tables"
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".mplconfig"))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


FAST_MODES = {
    "screen_board_default": ("Board", "Default 5×5"),
    "screen_board_dual_arena": ("Board", "Dual arena 5×7"),
    "screen_board_open_7x7": ("Board", "Open 7×7"),
    "screen_board_bottleneck_7x7": ("Board", "Bottleneck 7×7"),
    "screen_pieces_2": ("Pieces", "2 pieces"),
    "screen_pieces_4": ("Pieces", "4 pieces"),
    "screen_deck_movement": ("Deck", "Movement-heavy"),
    "screen_deck_capture": ("Deck", "Capture-heavy"),
    "screen_deck_swap": ("Deck", "Swap-heavy"),
    "screen_capture_score_1": ("Scoring", "Capture = 1"),
    "screen_capture_score_5": ("Scoring", "Capture = 5"),
    "screen_horizon_25": ("Horizon", "25 turns/player"),
    "screen_horizon_75": ("Horizon", "75 turns/player"),
}

SEARCH_MODES = {
    "search_board_default_25": ("Board", "Default 5×5"),
    "search_board_dual_arena_25": ("Board", "Dual arena 5×7"),
    "search_board_open_7x7_25": ("Board", "Open 7×7"),
    "search_board_bottleneck_7x7_25": ("Board", "Bottleneck 7×7"),
    "search_pieces_2_25": ("Pieces", "2 pieces"),
    "search_pieces_4_25": ("Pieces", "4 pieces"),
    "search_deck_movement_25": ("Deck", "Movement-heavy"),
    "search_deck_capture_25": ("Deck", "Capture-heavy"),
    "search_deck_swap_25": ("Deck", "Swap-heavy"),
}

BOARD_FILES = ["default", "dual_arena", "open_7x7", "bottleneck_7x7"]
SPREAD_BOARD_FILES = [
    "inner_ring_center_7x7",
    "inner_ring_multi_7x7",
    "outer_orbit_center_9x9",
    "outer_orbit_multi_9x9",
]
SPREAD_FAST_MODES = {
    "spread_inner_center_goal40": ("Inner ring", "Single center", 40),
    "spread_inner_multi_goal40": ("Inner ring", "Distributed", 40),
    "spread_outer_center_goal60": ("Outer orbit", "Single center", 60),
    "spread_outer_multi_goal60": ("Outer orbit", "Distributed", 60),
}
SPREAD_SEARCH_MODES = {
    "spread_search_inner_center_goal40": ("Single center", 40),
    "spread_search_inner_multi_goal40": ("Distributed", 40),
}
AGENT_COLORS = {"rule": "#59a14f", "greedy": "#4e79a7", "expectimax": "#e15759", "mcts": "#b07aa1"}


def ensure_dirs() -> None:
    FIGURES.mkdir(parents=True, exist_ok=True)
    TABLES.mkdir(parents=True, exist_ok=True)


def mode_config(mode: str) -> dict:
    return json.loads((ROOT / "modes" / mode / "config.json").read_text(encoding="utf-8"))


def load_mode_results(mode: str) -> pd.DataFrame:
    frames = []
    for path in sorted((ROOT / "modes" / mode / "results").glob("*.csv")):
        frame = pd.read_csv(path)
        frame["mode"] = mode
        frame["pair"] = path.stem
        frames.append(frame)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def to_long(results: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for row in results.itertuples(index=False):
        for player, seat, agent, opponent, score, opp_score, time_col, count_col in (
            (
                "A", "first", row.agent_a, row.agent_b, row.score_a, row.score_b,
                "decision_time_a_seconds", "decisions_a",
            ),
            (
                "B", "second", row.agent_b, row.agent_a, row.score_b, row.score_a,
                "decision_time_b_seconds", "decisions_b",
            ),
        ):
            outcome = 1.0 if row.winner == player else 0.5 if row.winner == "draw" else 0.0
            decision_time = float(getattr(row, time_col))
            decisions = int(getattr(row, count_col))
            rows.append(
                {
                    "mode": row.mode,
                    "pair": row.pair,
                    "game": int(row.game),
                    "agent": agent,
                    "opponent": opponent,
                    "seat": seat,
                    "outcome": outcome,
                    "score": int(score),
                    "margin": int(score) - int(opp_score),
                    "decision_time_seconds": decision_time,
                    "decisions": decisions,
                    "milliseconds_per_decision": 1000 * decision_time / decisions if decisions else np.nan,
                }
            )
    return pd.DataFrame(rows)


def final_pass_streak(path: Path) -> int:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    streak = 0
    for row in reversed(rows[1:]):
        if int(row["action"]) >= 0:
            break
        streak += 1
    return streak


def mode_deadlocks(mode: str) -> pd.DataFrame:
    rows = []
    for path in sorted((ROOT / "modes" / mode / "games").glob("*/*.csv")):
        streak = final_pass_streak(path)
        rows.append(
            {
                "mode": mode,
                "pair": path.parent.name,
                "game": int(path.stem),
                "final_pass_streak": streak,
                "deadlocked": streak >= 10,
            }
        )
    return pd.DataFrame(rows)


def summarize_fast() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    all_results = []
    all_deadlocks = []
    for mode, (family, condition) in FAST_MODES.items():
        results = load_mode_results(mode)
        if len(results) != 48:
            raise ValueError(f"{mode}: expected 48 results, found {len(results)}")
        results["family"] = family
        results["condition"] = condition
        all_results.append(results)
        deadlocks = mode_deadlocks(mode)
        deadlocks["family"] = family
        deadlocks["condition"] = condition
        all_deadlocks.append(deadlocks)
    results = pd.concat(all_results, ignore_index=True)
    long = to_long(results)
    meta = results[["mode", "family", "condition"]].drop_duplicates()
    long = long.merge(meta, on="mode")

    rg = long[
        long.agent.isin(["rule", "greedy"]) & long.opponent.isin(["rule", "greedy"])
    ]
    rule_greedy = (
        rg.groupby(["mode", "family", "condition", "agent"], as_index=False)
        .agg(
            games=("outcome", "size"),
            win_points_rate=("outcome", "mean"),
            mean_margin=("margin", "mean"),
            mean_ms_per_decision=("milliseconds_per_decision", "mean"),
        )
    )
    deadlocks = pd.concat(all_deadlocks, ignore_index=True)
    deadlock_summary = (
        deadlocks.groupby(["mode", "family", "condition"], as_index=False)
        .agg(games=("deadlocked", "size"), deadlock_rate=("deadlocked", "mean"), mean_final_pass_streak=("final_pass_streak", "mean"))
    )
    return results, rule_greedy, deadlock_summary


def summarize_search() -> tuple[pd.DataFrame, pd.DataFrame]:
    all_results = []
    for mode, (family, condition) in SEARCH_MODES.items():
        results = load_mode_results(mode)
        if len(results) != 18:
            raise ValueError(f"{mode}: expected 18 results, found {len(results)}")
        results["family"] = family
        results["condition"] = condition
        all_results.append(results)
    results = pd.concat(all_results, ignore_index=True)
    long = to_long(results)
    meta = results[["mode", "family", "condition"]].drop_duplicates()
    long = long.merge(meta, on="mode")
    summary = (
        long.groupby(["mode", "family", "condition", "agent"], as_index=False)
        .agg(
            games=("outcome", "size"),
            win_points_rate=("outcome", "mean"),
            mean_margin=("margin", "mean"),
            total_decision_time=("decision_time_seconds", "sum"),
            total_decisions=("decisions", "sum"),
        )
    )
    summary["milliseconds_per_decision"] = (
        1000 * summary.total_decision_time / summary.total_decisions
    )
    return results, summary


def summarize_expectimax_budget() -> pd.DataFrame:
    rows = []
    for depth in (1, 2, 3):
        mode = f"budget_expectimax_d{depth}"
        results = load_mode_results(mode)
        if len(results) != 6:
            raise ValueError(f"{mode}: expected 6 results, found {len(results)}")
        data = to_long(results)
        agent = data[data.agent == "expectimax"]
        rows.append(
            {
                "depth": depth,
                "top_k": 4,
                "games": len(agent),
                "win_points_rate": agent.outcome.mean(),
                "mean_margin": agent.margin.mean(),
                "milliseconds_per_decision": 1000 * agent.decision_time_seconds.sum() / agent.decisions.sum(),
                "total_decisions": int(agent.decisions.sum()),
            }
        )
    return pd.DataFrame(rows)


def summarize_mcts_budget() -> pd.DataFrame:
    rows = []
    for simulations in (50, 100, 200):
        for rollout in (5, 10, 20):
            mode = f"budget_mcts_s{simulations}_r{rollout}"
            results = load_mode_results(mode)
            if len(results) != 6:
                raise ValueError(f"{mode}: expected 6 results, found {len(results)}")
            data = to_long(results)
            agent = data[data.agent == "mcts"]
            rows.append(
                {
                    "simulations": simulations,
                    "rollout_depth": rollout,
                    "games": len(agent),
                    "win_points_rate": agent.outcome.mean(),
                    "mean_margin": agent.margin.mean(),
                    "milliseconds_per_decision": 1000 * agent.decision_time_seconds.sum() / agent.decisions.sum(),
                    "total_decisions": int(agent.decisions.sum()),
                }
            )
    return pd.DataFrame(rows)


def summarize_refresh_rule() -> tuple[pd.DataFrame, pd.DataFrame]:
    comparisons = [
        ("Default", "Original pass rule", "screen_board_default"),
        ("Default", "Refresh after 2 passes", "refresh2_default"),
        ("Capture-heavy", "Original pass rule", "screen_deck_capture"),
        ("Capture-heavy", "Refresh after 2 passes", "refresh2_capture_heavy"),
    ]
    rows = []
    for environment, rule, mode in comparisons:
        results = load_mode_results(mode)
        deadlocks = mode_deadlocks(mode)
        rows.append(
            {
                "environment": environment,
                "pass_rule": rule,
                "mode": mode,
                "games": len(results),
                "draw_rate": results.winner.eq("draw").mean(),
                "deadlock_rate": deadlocks.deadlocked.mean(),
                "mean_final_pass_streak": deadlocks.final_pass_streak.mean(),
                "mean_total_score": (results.score_a + results.score_b).mean(),
            }
        )

    search_rows = []
    for rule, mode in (
        ("Original pass rule", "search_deck_capture_25"),
        ("Refresh after 2 passes", "refresh2_search_capture_25"),
    ):
        data = to_long(load_mode_results(mode))
        for agent in ("rule", "expectimax", "mcts"):
            subset = data[data.agent == agent]
            search_rows.append(
                {
                    "pass_rule": rule,
                    "mode": mode,
                    "agent": agent,
                    "games": len(subset),
                    "win_points_rate": subset.outcome.mean(),
                    "mean_margin": subset.margin.mean(),
                    "milliseconds_per_decision": 1000
                    * subset.decision_time_seconds.sum()
                    / subset.decisions.sum(),
                    "mean_decisions_per_game": subset.decisions.mean(),
                }
            )
    return pd.DataFrame(rows), pd.DataFrame(search_rows)


def summarize_spread_goals() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    result_rows = []
    search_rows = []
    for mode, (geometry, objectives, goal) in SPREAD_FAST_MODES.items():
        results = load_mode_results(mode)
        if len(results) != 48:
            raise ValueError(f"{mode}: expected 48 results, found {len(results)}")
        for row in results.itertuples(index=False):
            result_rows.append(
                {
                    "mode": mode,
                    "geometry": geometry,
                    "objectives": objectives,
                    "score_goal": goal,
                    "game": row.game,
                    "agent_a": row.agent_a,
                    "agent_b": row.agent_b,
                    "winner": row.winner,
                    "score_a": row.score_a,
                    "score_b": row.score_b,
                    "turns_a": row.turns_a,
                    "turns_b": row.turns_b,
                    "total_turns": row.turns_a + row.turns_b,
                    "goal_reached": max(row.score_a, row.score_b) >= goal,
                }
            )
    for mode, (objectives, goal) in SPREAD_SEARCH_MODES.items():
        results = load_mode_results(mode)
        if len(results) != 18:
            raise ValueError(f"{mode}: expected 18 results, found {len(results)}")
        data = to_long(results)
        for agent, subset in data.groupby("agent"):
            search_rows.append(
                {
                    "mode": mode,
                    "objectives": objectives,
                    "score_goal": goal,
                    "agent": agent,
                    "games": len(subset),
                    "win_points_rate": subset.outcome.mean(),
                    "mean_margin": subset.margin.mean(),
                    "milliseconds_per_decision": 1000
                    * subset.decision_time_seconds.sum()
                    / subset.decisions.sum(),
                }
            )
    raw = pd.DataFrame(result_rows)
    summary = (
        raw.groupby(["geometry", "objectives", "score_goal"], as_index=False)
        .agg(
            games=("game", "size"),
            decisive_rate=("winner", lambda x: (x != "draw").mean()),
            goal_reached_rate=("goal_reached", "mean"),
            mean_total_turns=("total_turns", "mean"),
            median_total_turns=("total_turns", "median"),
            mean_winning_score=("score_a", "mean"),
        )
    )
    # Replace the placeholder with the actual winning score.
    winning_scores = raw.apply(
        lambda row: row.score_a if row.winner == "A" else row.score_b if row.winner == "B" else max(row.score_a, row.score_b),
        axis=1,
    )
    raw["winning_score"] = winning_scores
    summary = summary.drop(columns="mean_winning_score").merge(
        raw.groupby(["geometry", "objectives", "score_goal"], as_index=False)
        .winning_score.mean()
        .rename(columns={"winning_score": "mean_winning_score"}),
        on=["geometry", "objectives", "score_goal"],
    )
    return raw, summary, pd.DataFrame(search_rows)


def summarize_expectimax_feasibility() -> pd.DataFrame:
    measured = {
        2: (1.166, 240, "completed"),
        3: (10.274, 3615, "completed"),
        4: (102.444, 53545, "completed"),
        5: (120.0, np.nan, "timeout >120 s"),
        6: (np.nan, np.nan, "skipped after depth-5 timeout"),
    }
    match_modes = {
        2: "spread_expectimax_d2_goal20",
        3: "spread_expectimax_d3_goal20",
        4: "spread_expectimax_d4_goal20",
    }
    rows = []
    for depth in range(2, 7):
        seconds, nodes, status = measured[depth]
        row = {
            "depth": depth,
            "benchmark_seconds": seconds,
            "benchmark_nodes": nodes,
            "benchmark_status": status,
            "bounded_match_games": 0,
            "bounded_match_win_points": np.nan,
            "bounded_match_seconds_per_game": np.nan,
            "bounded_match_ms_per_decision": np.nan,
        }
        if depth in match_modes:
            results = load_mode_results(match_modes[depth])
            data = to_long(results)
            agent = data[data.agent == "expectimax"]
            row.update(
                {
                    "bounded_match_games": len(results),
                    "bounded_match_win_points": agent.outcome.mean(),
                    "bounded_match_seconds_per_game": (
                        results.decision_time_a_seconds + results.decision_time_b_seconds
                    ).mean(),
                    "bounded_match_ms_per_decision": 1000
                    * agent.decision_time_seconds.sum()
                    / agent.decisions.sum(),
                }
            )
        rows.append(row)
    return pd.DataFrame(rows)


def summarize_net_usage() -> pd.DataFrame:
    rows = []
    modes = list(SPREAD_FAST_MODES) + list(SPREAD_SEARCH_MODES)
    for mode in modes:
        config = mode_config(mode)
        board = config["board"]["name"]
        for path in sorted((ROOT / "modes" / mode / "games").glob("*/*.csv")):
            agent_a, agent_b = path.parent.name.split("_", 1)
            with path.open(newline="", encoding="utf-8") as handle:
                game_rows = list(csv.DictReader(handle))
            for row in game_rows[1:]:
                if row["card_drawn"] != "capture":
                    continue
                player = int(row["player"])
                # Each row describes the preceding move, made by the other player.
                actor_seat = 1 - player
                rows.append(
                    {
                        "mode": mode,
                        "board": board,
                        "agent": agent_a if actor_seat == 0 else agent_b,
                        "capture_type": "net" if row["src_1"] not in ("", "-1", "None") else "adjacent",
                    }
                )
    raw = pd.DataFrame(rows)
    counts = (
        raw.groupby(["agent", "capture_type"]).size().unstack(fill_value=0)
        if not raw.empty
        else pd.DataFrame()
    )
    for column in ("net", "adjacent"):
        if column not in counts:
            counts[column] = 0
    counts = counts.reset_index()
    counts["total_captures"] = counts["net"] + counts["adjacent"]
    counts["net_share"] = counts["net"] / counts["total_captures"]
    return counts.sort_values("agent")


def plot_boards() -> None:
    fig, axes = plt.subplots(1, 4, figsize=(15, 4.6))
    for ax, name in zip(axes, BOARD_FILES):
        board = json.loads((ROOT / "boards" / f"{name}.json").read_text(encoding="utf-8"))
        rows, cols = board["rows"], board["cols"]
        ax.set_xlim(-0.5, cols - 0.5)
        ax.set_ylim(rows - 0.5, -0.5)
        ax.set_aspect("equal")
        ax.set_xticks(np.arange(-0.5, cols, 1), minor=True)
        ax.set_yticks(np.arange(-0.5, rows, 1), minor=True)
        ax.grid(which="minor", color="#b8b8b8", linewidth=1)
        ax.set_xticks([])
        ax.set_yticks([])
        for r, c in board.get("blocked_cells", []):
            ax.add_patch(plt.Rectangle((c - 0.5, r - 0.5), 1, 1, color="#333333"))
        for player, color in (("A", "#4e79a7"), ("B", "#e15759")):
            for r, c in board["spawns"][player]:
                ax.add_patch(plt.Circle((c, r), 0.28, color=color))
                ax.text(c, r, player, color="white", ha="center", va="center", fontweight="bold", fontsize=8)
        for entry in board["capture_cells"]:
            r, c = entry["cell"]
            ax.add_patch(plt.Rectangle((c - 0.43, r - 0.43), 0.86, 0.86, color="#f1ce63", alpha=0.9))
            ax.text(c, r, f"+{entry['points']}", ha="center", va="center", fontweight="bold")
        ax.set_title(board["name"].replace("_", " "), fontsize=11, fontweight="bold")
    fig.suptitle("Board configurations used in the screening experiments", fontsize=14)
    fig.tight_layout()
    fig.savefig(FIGURES / "01_board_designs.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def plot_rule_greedy(summary: pd.DataFrame) -> None:
    order = [(family, condition) for _, (family, condition) in FAST_MODES.items()]
    labels = [condition for _, condition in order]
    fig, ax = plt.subplots(figsize=(12, 6.5))
    y = np.arange(len(labels))
    height = 0.35
    for offset, agent in ((-height / 2, "rule"), (height / 2, "greedy")):
        values = []
        for family, condition in order:
            row = summary[
                (summary.family == family) & (summary.condition == condition) & (summary.agent == agent)
            ].iloc[0]
            values.append(row.win_points_rate * 100)
        ax.barh(y + offset, values, height, label=agent, color=AGENT_COLORS[agent])
    for index in (3, 5, 8, 10):
        ax.axhline(index + 0.5, color="#cccccc", linewidth=1)
    ax.axvline(50, color="black", linestyle="--", linewidth=1)
    ax.set_yticks(y, labels)
    ax.invert_yaxis()
    ax.set_xlabel("Win points in rule–greedy matchup (%)")
    ax.set_title("Rule versus greedy across environment factors\n16 games per condition (8 seeds × both orientations)", loc="left", fontweight="bold")
    ax.legend(frameon=False)
    ax.grid(axis="x", alpha=0.25)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(FIGURES / "02_rule_vs_greedy_factors.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def plot_deadlocks(summary: pd.DataFrame) -> None:
    order = [(family, condition) for _, (family, condition) in FAST_MODES.items()]
    labels = [condition for _, condition in order]
    values = [
        summary[(summary.family == family) & (summary.condition == condition)].iloc[0].deadlock_rate * 100
        for family, condition in order
    ]
    fig, ax = plt.subplots(figsize=(11, 5.8))
    colors = ["#e15759" if condition == "Capture-heavy" else "#76b7b2" for _, condition in order]
    ax.bar(np.arange(len(labels)), values, color=colors)
    ax.set_xticks(np.arange(len(labels)), labels, rotation=40, ha="right")
    ax.set_ylabel("Games with final pass streak ≥10 (%)")
    ax.set_title("Absorbing-market deadlocks across factors\n48 games per condition", loc="left", fontweight="bold")
    ax.grid(axis="y", alpha=0.25)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(FIGURES / "03_deadlocks_by_factor.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def plot_search_family(summary: pd.DataFrame, family: str, filename: str) -> None:
    data = summary[summary.family == family]
    conditions = list(dict.fromkeys(data.condition))
    agents = ["rule", "expectimax", "mcts"]
    x = np.arange(len(conditions))
    width = 0.25
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.2))
    for i, agent in enumerate(agents):
        subset = data[data.agent == agent].set_index("condition").loc[conditions]
        axes[0].bar(x + (i - 1) * width, subset.win_points_rate * 100, width, label=agent, color=AGENT_COLORS[agent])
        axes[1].bar(x + (i - 1) * width, subset.milliseconds_per_decision, width, label=agent, color=AGENT_COLORS[agent])
    axes[0].axhline(50, color="black", linestyle="--", linewidth=1)
    axes[0].set_ylabel("Win points across two opponents (%)")
    axes[1].set_ylabel("Weighted mean ms/decision")
    axes[1].set_yscale("log")
    for ax in axes:
        ax.set_xticks(x, conditions, rotation=30, ha="right")
        ax.grid(axis="y", alpha=0.25)
        ax.spines[["top", "right"]].set_visible(False)
    axes[0].set_title(f"{family}: playing strength", loc="left", fontweight="bold")
    axes[1].set_title(f"{family}: decision cost (log scale)", loc="left", fontweight="bold")
    axes[0].legend(frameon=False)
    fig.suptitle("Search-agent screening: 3 seeds, both orientations, 25 turns/player", fontsize=13)
    fig.tight_layout()
    fig.savefig(FIGURES / filename, dpi=220, bbox_inches="tight")
    plt.close(fig)


def plot_expectimax_budget(data: pd.DataFrame) -> None:
    fig, ax1 = plt.subplots(figsize=(8, 5.2))
    ax2 = ax1.twinx()
    ax1.plot(data.depth, data.win_points_rate * 100, marker="o", linewidth=2.2, color=AGENT_COLORS["expectimax"], label="Win points")
    ax2.plot(data.depth, data.milliseconds_per_decision, marker="s", linewidth=2.2, color="#333333", label="Decision time")
    ax1.set_xticks(data.depth)
    ax1.set_xlabel("Expectimax depth (top_k = 4)")
    ax1.set_ylabel("Win points vs rule (%)", color=AGENT_COLORS["expectimax"])
    ax2.set_ylabel("Weighted mean ms/decision", color="#333333")
    ax2.set_yscale("log")
    ax1.axhline(50, color="#888888", linestyle="--", linewidth=1)
    ax1.grid(axis="y", alpha=0.25)
    ax1.spines["top"].set_visible(False)
    ax2.spines["top"].set_visible(False)
    ax1.set_title("Expectimax depth trade-off\n6 games per setting; default board; 15 turns/player", loc="left", fontweight="bold")
    fig.tight_layout()
    fig.savefig(FIGURES / "06_expectimax_depth_tradeoff.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def plot_mcts_budget(data: pd.DataFrame) -> None:
    win = data.pivot(index="rollout_depth", columns="simulations", values="win_points_rate").sort_index()
    runtime = data.pivot(index="rollout_depth", columns="simulations", values="milliseconds_per_decision").sort_index()
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.8))
    for ax, matrix, title, cmap in (
        (axes[0], win * 100, "Win points vs rule (%)", "RdYlGn"),
        (axes[1], runtime, "Mean ms/decision", "YlOrRd"),
    ):
        image = ax.imshow(matrix.to_numpy(), aspect="auto", cmap=cmap)
        for i in range(len(matrix.index)):
            for j in range(len(matrix.columns)):
                value = matrix.iloc[i, j]
                label = f"{value:.0f}" if ax is axes[0] else f"{value:.1f}"
                ax.text(j, i, label, ha="center", va="center", fontsize=9)
        ax.set_xticks(range(len(matrix.columns)), matrix.columns)
        ax.set_yticks(range(len(matrix.index)), matrix.index)
        ax.set_xlabel("Simulations")
        ax.set_ylabel("Rollout depth")
        ax.set_title(title, fontweight="bold")
        fig.colorbar(image, ax=ax, shrink=0.8)
    fig.suptitle("MCTS budget screen: 6 games per cell; default board; 15 turns/player", fontsize=13)
    fig.tight_layout()
    fig.savefig(FIGURES / "07_mcts_budget_heatmaps.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def plot_refresh_rule(refresh: pd.DataFrame, search: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.2))
    conditions = [
        ("Default", "Original pass rule"),
        ("Default", "Refresh after 2 passes"),
        ("Capture-heavy", "Original pass rule"),
        ("Capture-heavy", "Refresh after 2 passes"),
    ]
    labels = ["Default\noriginal", "Default\nrefresh", "Capture-heavy\noriginal", "Capture-heavy\nrefresh"]
    deadlocks = [
        refresh[(refresh.environment == environment) & (refresh.pass_rule == rule)].iloc[0].deadlock_rate * 100
        for environment, rule in conditions
    ]
    draws = [
        refresh[(refresh.environment == environment) & (refresh.pass_rule == rule)].iloc[0].draw_rate * 100
        for environment, rule in conditions
    ]
    x = np.arange(len(labels))
    width = 0.36
    axes[0].bar(x - width / 2, deadlocks, width, label="Deadlocked", color="#e15759")
    axes[0].bar(x + width / 2, draws, width, label="Draw", color="#bab0ab")
    axes[0].set_xticks(x, labels)
    axes[0].set_ylabel("Games (%)")
    axes[0].set_title("Deadlocks and draws", loc="left", fontweight="bold")
    axes[0].legend(frameon=False)

    agents = ["rule", "expectimax", "mcts"]
    x2 = np.arange(len(agents))
    for offset, rule, color in (
        (-width / 2, "Original pass rule", "#9c9c9c"),
        (width / 2, "Refresh after 2 passes", "#4e79a7"),
    ):
        subset = search[search.pass_rule == rule].set_index("agent").loc[agents]
        axes[1].bar(x2 + offset, subset.win_points_rate * 100, width, label=rule, color=color)
    axes[1].axhline(50, color="black", linestyle="--", linewidth=1)
    axes[1].set_xticks(x2, agents)
    axes[1].set_ylabel("Win points across two opponents (%)")
    axes[1].set_title("Capture-heavy search screen", loc="left", fontweight="bold")
    axes[1].legend(frameon=False, fontsize=8)
    for ax in axes:
        ax.grid(axis="y", alpha=0.25)
        ax.spines[["top", "right"]].set_visible(False)
    fig.suptitle("Effect of refreshing the full market after two consecutive passes", fontsize=13)
    fig.tight_layout()
    fig.savefig(FIGURES / "08_two_pass_refresh_effect.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def plot_spread_boards() -> None:
    fig, axes = plt.subplots(1, 4, figsize=(16, 4.8))
    for ax, name in zip(axes, SPREAD_BOARD_FILES):
        board = json.loads((ROOT / "boards" / f"{name}.json").read_text(encoding="utf-8"))
        rows, cols = board["rows"], board["cols"]
        ax.set_xlim(-0.5, cols - 0.5)
        ax.set_ylim(rows - 0.5, -0.5)
        ax.set_aspect("equal")
        ax.set_xticks(np.arange(-0.5, cols, 1), minor=True)
        ax.set_yticks(np.arange(-0.5, rows, 1), minor=True)
        ax.grid(which="minor", color="#c8c8c8", linewidth=0.8)
        ax.set_xticks([])
        ax.set_yticks([])
        for player, color in (("A", "#4e79a7"), ("B", "#e15759")):
            for r, c in board["spawns"][player]:
                ax.add_patch(plt.Circle((c, r), 0.3, color=color, zorder=3))
                ax.text(c, r, player, color="white", ha="center", va="center", fontweight="bold", fontsize=8, zorder=4)
        for entry in board["capture_cells"]:
            r, c = entry["cell"]
            ax.add_patch(plt.Rectangle((c - 0.42, r - 0.42), 0.84, 0.84, color="#f1ce63", alpha=0.9, zorder=2))
            ax.text(c, r, f"+{entry['points']}", ha="center", va="center", fontweight="bold", zorder=5)
        ax.set_title(board["name"].replace("_", " "), fontsize=10, fontweight="bold")
    fig.suptitle("Spread-spawn boards: ring/orbit geometry and objective variants", fontsize=14)
    fig.tight_layout()
    fig.savefig(FIGURES / "09_spread_spawn_boards.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def plot_point_goals(summary: pd.DataFrame, search: pd.DataFrame) -> None:
    labels = [
        f"{row.geometry}\n{row.objectives}"
        for row in summary.itertuples(index=False)
    ]
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.1))
    x = np.arange(len(summary))
    axes[0].bar(x, summary.mean_total_turns, color=["#4e79a7", "#76b7b2", "#4e79a7", "#76b7b2"])
    axes[0].set_xticks(x, labels)
    axes[0].set_ylabel("Mean turns taken (both players)")
    axes[0].set_title("Time to score goal", loc="left", fontweight="bold")
    agents = ["rule", "expectimax", "mcts"]
    width = 0.25
    conditions = ["Single center", "Distributed"]
    for i, agent in enumerate(agents):
        subset = search[search.agent == agent].set_index("objectives").loc[conditions]
        axes[1].bar(np.arange(2) + (i - 1) * width, subset.win_points_rate * 100, width, label=agent, color=AGENT_COLORS[agent])
    axes[1].axhline(50, color="black", linestyle="--", linewidth=1)
    axes[1].set_xticks(np.arange(2), conditions)
    axes[1].set_ylabel("Win points across two opponents (%)")
    axes[1].set_title("Search agents on inner-ring goals", loc="left", fontweight="bold")
    axes[1].legend(frameon=False)
    for ax in axes:
        ax.grid(axis="y", alpha=0.25)
        ax.spines[["top", "right"]].set_visible(False)
    fig.suptitle("Point-goal experiments with two-pass market refresh", fontsize=13)
    fig.tight_layout()
    fig.savefig(FIGURES / "10_point_goal_results.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def plot_expectimax_feasibility(data: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(8.5, 5.2))
    completed = data[data.benchmark_status == "completed"]
    ax.plot(completed.depth, completed.benchmark_seconds, marker="o", linewidth=2.4, color=AGENT_COLORS["expectimax"])
    timeout = data[data.depth == 5].iloc[0]
    ax.scatter([timeout.depth], [timeout.benchmark_seconds], marker="x", s=100, linewidth=2.5, color="#e15759", label="Timed out")
    ax.annotate(">120 s timeout", (5, timeout.benchmark_seconds), xytext=(4.35, 42), arrowprops={"arrowstyle": "->"})
    ax.text(6, 120, "not attempted", ha="center", va="bottom", color="#666666")
    ax.set_yscale("log")
    ax.set_xticks(range(2, 7))
    ax.set_xlabel("Expectimax depth (single-decision benchmark, top-k 3)")
    ax.set_ylabel("Seconds")
    ax.set_title("Exact chance expansion becomes infeasible beyond depth 4", loc="left", fontweight="bold")
    ax.grid(axis="y", alpha=0.25)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(FIGURES / "11_expectimax_depth_2_to_6_feasibility.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def plot_net_usage(data: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(8.5, 5.0))
    x = np.arange(len(data))
    ax.bar(x, data.adjacent, label="Adjacent capture", color="#76b7b2")
    ax.bar(x, data.net, bottom=data.adjacent, label="Net launcher", color="#f28e2b")
    for i, row in enumerate(data.itertuples(index=False)):
        ax.text(i, row.total_captures + 0.6, f"{row.net_share:.0%} net", ha="center", fontsize=9)
    ax.set_xticks(x, data.agent)
    ax.set_ylabel("Capture actions in 228 spread-board games")
    ax.set_title("Agents differ in their use of the net launcher", loc="left", fontweight="bold")
    ax.legend(frameon=False)
    ax.grid(axis="y", alpha=0.25)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(FIGURES / "12_net_launcher_usage.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def write_analysis(
    fast_results: pd.DataFrame,
    rule_greedy: pd.DataFrame,
    deadlocks: pd.DataFrame,
    search_summary: pd.DataFrame,
    expectimax: pd.DataFrame,
    mcts: pd.DataFrame,
    refresh: pd.DataFrame,
    refresh_search: pd.DataFrame,
    spread_summary: pd.DataFrame,
    spread_search: pd.DataFrame,
    feasibility: pd.DataFrame,
    net_usage: pd.DataFrame,
) -> None:
    rg_pivot = rule_greedy.pivot(index=["family", "condition"], columns="agent", values="win_points_rate")
    default_rule = rg_pivot.loc[("Board", "Default 5×5"), "rule"]
    dual_greedy = rg_pivot.loc[("Board", "Dual arena 5×7"), "greedy"]
    open_greedy = rg_pivot.loc[("Board", "Open 7×7"), "greedy"]
    bottleneck_greedy = rg_pivot.loc[("Board", "Bottleneck 7×7"), "greedy"]
    capture_deadlock = deadlocks[deadlocks.condition == "Capture-heavy"].iloc[0].deadlock_rate
    default_deadlock = deadlocks[deadlocks.condition == "Default 5×5"].iloc[0].deadlock_rate
    exp_best = expectimax.sort_values(["win_points_rate", "mean_margin"], ascending=False).iloc[0]
    exp_cost_ratio = expectimax.set_index("depth").loc[3, "milliseconds_per_decision"] / expectimax.set_index("depth").loc[2, "milliseconds_per_decision"]
    mcts_best = mcts.sort_values(["win_points_rate", "mean_margin"], ascending=False).iloc[0]
    refresh_table = refresh.set_index(["environment", "pass_rule"])
    legacy_capture = refresh_table.loc[("Capture-heavy", "Original pass rule")]
    fixed_capture = refresh_table.loc[("Capture-heavy", "Refresh after 2 passes")]
    spread_fastest = spread_summary.sort_values("mean_total_turns").iloc[0]
    depth4 = feasibility[feasibility.depth == 4].iloc[0]
    net_total = int(net_usage.net.sum())
    capture_total = int(net_usage.total_captures.sum())

    text = f"""# Future experiments: screening results

## Scope and status

This is an **exploratory screening study**, not the final confirmatory experiment. It contains **1,206 newly run games**:

- 624 fast-agent robustness games (`random`, `greedy`, `rule`) across boards, piece counts, decks, scoring values, and horizons;
- 162 targeted search-agent games (`rule`, `expectimax`, `mcts`) across boards, piece counts, and decks;
- 72 parameter games for expectimax depth and the MCTS simulations × rollout-depth grid.
- 114 matched games evaluating the selected two-pass market-refresh rule.
- 234 games covering spread-spawn boards, point-goal wins, and bounded expectimax depths 2-4.

The flawed minimax agent is excluded. Every new results row records the time spent by each agent choosing actions and its number of non-pass decisions. Search screens use three seeds and shortened horizons to identify promising conditions economically. Percentages can therefore move sharply with one game and must not be presented as precise population estimates.

## 1. Board designs

Figure 01 shows the default board and three strategic variants:

- `dual_arena`: two equal 2-point objectives separated by a blocked center;
- `open_7x7`: a larger open arena with a 2-point center and two 1-point side objectives;
- `bottleneck_7x7`: three passages across a blocked middle row, with a 3-point central passage.

Two additional 5×5 definitions change the piece count to two and four. All boards are symmetric between players, so move-order effects are not intentionally built into the geometry.

## 2. Robustness of the rule–greedy result

The baseline conclusion that `rule` dominates `greedy` is **environment-dependent**. On the default board, rule received {default_rule:.0%} of win points across their 16 direct games. Greedy received {dual_greedy:.0%} on the dual arena, {open_greedy:.0%} on the open 7×7 board, and {bottleneck_greedy:.0%} on the bottleneck board.

This reversal is substantively plausible. Rule’s fixed “capture, then objective” priority is well matched to a single recurring center. With several separated objectives, greedy’s full heuristic can trade off movement, threats, safety, and objective values more flexibly. The result justifies promoting board × agent interaction—not one global ranking—to a main report question.

Figure 02 covers the remaining factors. It should be read for large reversals only; eight seeds are insufficient for close conditions.

## 3. Deadlocks and deck composition

The capture-heavy deck is the clearest failure condition: {capture_deadlock:.0%} of its 48 games end with at least 10 consecutive passes, compared with {default_deadlock:.0%} for the default-board control. Figure 03 confirms that card supply strongly affects whether the market enters an absorbing illegal state.

This supports a concrete design change before confirmatory testing: either discard/redraw one unavailable market card after a pass, refresh the market after both players pass, or terminate and score the game when the state is provably stuck. The original pass rule should remain as a labeled control.

### Selected rule and matched validation

The selected rule is now implemented as an optional mode parameter: **after two consecutive passes, discard the entire three-card market, deal three replacements, reset the counter, and continue**. Any legal action resets the counter immediately. Old modes omit the parameter and therefore replay with the original behavior.

In the matched capture-heavy fast screen, deadlocks fell from {legacy_capture.deadlock_rate:.0%} to {fixed_capture.deadlock_rate:.0%}, while draws fell from {legacy_capture.draw_rate:.0%} to {fixed_capture.draw_rate:.0%}. Figure 08 shows the corresponding default-deck control and the search-agent outcome comparison. Eliminating deadlocks increases actual decisions and therefore whole-game runtime; this is desired because the match is continuing rather than idling through passes.

## 4. Search agents across environments

Figures 04 and 05 compare `rule`, depth-2/top-6 `expectimax`, and MCTS with 100 simulations and rollout depth 10. Each agent has 12 observations per condition (two opponents, both orientations, three seeds).

The rankings change across boards and decks, while runtime changes with branching and pass frequency. In particular, four pieces substantially increase decision cost, and capture-heavy deadlocks make agents appear artificially fast because many scheduled turns require no decision. Runtime must therefore be reported per actual decision alongside pass rate—not only per match.

The three-seed results are useful for selecting confirmatory conditions, but they are too small to assert that one search agent is generally superior.

## 5. Expectimax depth

The best observed expectimax screen is depth {int(exp_best.depth)} at {exp_best.win_points_rate:.0%} win points against rule. Depth 3 costs {exp_cost_ratio:.1f}× as much per decision as depth 2 in this screen. With only six games per depth, the outcome curve is noisy; the reliable conclusion is computational: exact chance expansion becomes expensive very quickly even after limiting each decision node to the top four actions.

Recommended confirmatory comparison: depths 1–3, 30–50 paired seeds, fixed top-k, and both a fixed-depth and equal-time presentation.

## 6. MCTS budget

The strongest observed MCTS cell is {int(mcts_best.simulations)} simulations with rollout depth {int(mcts_best.rollout_depth)}, scoring {mcts_best.win_points_rate:.0%} win points against rule. Figure 07 shows that simulations drive a near-linear cost increase, while greater rollout depth adds cost without a monotonic strength guarantee in this small sample.

Do not select the numerically highest cell and report it as proven optimal: nine cells were screened on only six games each. Instead, select two Pareto-efficient settings—one inexpensive and one high-budget—and rerun both with substantially more seeds.

## 7. Recommended confirmatory batch

Prioritize the following:

1. Default versus dual-arena versus open-7×7 boards, because the rule–greedy ranking reverses.
2. Default versus capture-heavy deck under both the original and revised pass rule.
3. Rule, greedy, expectimax depth 2, and two MCTS budgets; 50 paired seeds, both orientations.
4. Default three pieces versus four pieces, with per-decision runtime and legal-action counts.
5. Equal-time search comparisons after fixed-parameter results.

Use win points, score margin, time-to-goal, deadlock rate, scoring-source decomposition, adjacent/net capture counts, and milliseconds per actual decision. Treat seed as a paired block. Run both fixed-horizon and `score_to_win` modes because they answer different questions.

## 8. Spread spawns, objective values, and point-goal wins

Figure 09 introduces two symmetric spawn geometries. The 7x7 **inner ring** places each side on an opposing arc near the middle; the 9x9 **outer orbit** spreads the pieces farther around the objective. Each geometry has a concentrated objective, where holding the center is worth more than a capture (`capture_score = 1`), and a distributed-objective control.

The optional `score_to_win` rule now ends a match as soon as either score reaches its configured goal, while the turn limit remains a safety cap. All 192 fast-agent games ended decisively. The fastest condition was {spread_fastest.geometry} / {spread_fastest.objectives}, reaching its goal after {spread_fastest.mean_total_turns:.1f} combined turns on average. Figure 10 and Table 11 report time-to-goal and agent outcomes. Because the inner and outer conditions use goals of 40 and 60 respectively, compare objective variants within a geometry, not raw turn counts across geometries.

## 9. Expectimax depths 2-6

A controlled single-decision benchmark took 1.166 s at depth 2, 10.274 s at depth 3, and 102.444 s at depth 4. Depth 5 exceeded the 120-second limit; depth 6 was skipped after that timeout. Even under a smaller top-2 action cap and a score goal of 20, the two depth-4 games averaged {depth4.bounded_match_seconds_per_game:.1f} seconds of measured decision time.

This establishes the feasible experimental boundary: use depths 2-3 for replicated full matches, depth 4 only as a tightly bounded computational demonstration, and do not spend the project budget on depths 5-6 without approximation, sampling, caching, or a strict time budget.

## 10. Net-launcher statistics

The game-log analysis now distinguishes adjacent captures from net launches by checking whether the capture move records a second source piece (the launcher). Across the 228 new spread-board fast/search games, agents made {capture_total} capture actions, of which {net_total} ({net_total / capture_total:.1%}) used the net. Figure 12 and Table 13 break this down by agent. Counts should be reported beside shares: an agent can have a high net share simply because it captures rarely.

## 11. Reproduction

All mode directories contain immutable board/deck snapshots, parameters, seeds, results, and per-turn games. Regenerate this package with:

```powershell
python analysis/future_experiments_report.py
```
"""
    (OUT / "01_ANALYSIS.md").write_text(text, encoding="utf-8")


def write_indexes() -> None:
    files = [
        ("01_ANALYSIS.md", "Interpretation, limitations, and confirmatory recommendations"),
        ("figures/01_board_designs.png", "Visual map of the four board geometries"),
        ("figures/02_rule_vs_greedy_factors.png", "Rule–greedy robustness across factors"),
        ("figures/03_deadlocks_by_factor.png", "Absorbing-market deadlock rates"),
        ("figures/04_search_agents_boards.png", "Search-agent strength and runtime across boards"),
        ("figures/05_search_agents_pieces.png", "Search-agent strength and runtime by piece count"),
        ("figures/05b_search_agents_decks.png", "Search-agent strength and runtime by deck"),
        ("figures/06_expectimax_depth_tradeoff.png", "Expectimax strength–depth–runtime trade-off"),
        ("figures/07_mcts_budget_heatmaps.png", "MCTS budget strength and runtime heatmaps"),
        ("figures/08_two_pass_refresh_effect.png", "Matched validation of the selected market-refresh rule"),
        ("figures/09_spread_spawn_boards.png", "Four ring/orbit spawn and objective designs"),
        ("figures/10_point_goal_results.png", "Time-to-goal and search-agent outcomes"),
        ("figures/11_expectimax_depth_2_to_6_feasibility.png", "Measured feasibility boundary for depths 2-6"),
        ("figures/12_net_launcher_usage.png", "Adjacent versus net-launcher captures by agent"),
        ("tables/01_fast_rule_greedy.csv", "Direct rule–greedy factor results"),
        ("tables/02_deadlocks.csv", "Deadlock summary by fast-screen factor"),
        ("tables/03_search_factors.csv", "Search-agent outcomes and measured runtime"),
        ("tables/04_expectimax_depth.csv", "Expectimax depth screen"),
        ("tables/05_mcts_budget.csv", "MCTS parameter grid"),
        ("tables/06_all_fast_results.csv", "Raw aggregate results from fast-screen modes"),
        ("tables/07_all_search_results.csv", "Raw aggregate results from search-screen modes"),
        ("tables/08_refresh_rule_comparison.csv", "Matched deadlock/draw comparison"),
        ("tables/09_refresh_search_comparison.csv", "Search-agent results under original and refreshed markets"),
        ("tables/10_spread_point_goal_results.csv", "Raw point-goal results on spread-spawn boards"),
        ("tables/11_spread_point_goal_summary.csv", "Time-to-goal summary by geometry and objective"),
        ("tables/12_spread_search_agents.csv", "Search-agent outcomes on inner-ring objective variants"),
        ("tables/13_net_launcher_usage.csv", "Net and adjacent capture counts by agent"),
        ("tables/14_expectimax_depth_2_to_6.csv", "Benchmark and bounded-match feasibility evidence"),
        ("../../analysis/future_experiments_report.py", "Reproduction script"),
    ]
    lines = "\n".join(f"- [{path}]({path}) — {description}" for path, description in files)
    text = f"""# Future-experiment results index

Start with [01_ANALYSIS.md](01_ANALYSIS.md). This package contains exploratory results from 1,206 new games. Minimax is excluded; timing is measured natively per agent and decision.

## Files

{lines}

## Experimental tiers

- Fast robustness screens: 8 seeds, both orientations, 50 turns/player except explicit horizon modes.
- Search factor screens: 3 seeds, both orientations, 25 turns/player, expectimax depth 2/top-k 6, MCTS 100 simulations/depth 10.
- Budget screens: 3 seeds, both orientations, 15 turns/player.

These are screening samples. Use them to select confirmatory experiments, not as final precise rankings.
"""
    (OUT / "00_INDEX.md").write_text(text, encoding="utf-8")

    root_index = """# Final results

- [Baseline full analysis](baseline_full/00_INDEX.md) — original 1,080-game baseline, including the minimax validity warning.
- [Future-experiment screening](future_experiments/00_INDEX.md) — new boards, point-goal wins, net-launcher use, measured runtime, expectimax depth, and MCTS budgets.
"""
    (ROOT / "final_results" / "00_INDEX.md").write_text(root_index, encoding="utf-8")


def main() -> None:
    ensure_dirs()
    fast_results, rule_greedy, deadlocks = summarize_fast()
    search_results, search_summary = summarize_search()
    expectimax = summarize_expectimax_budget()
    mcts = summarize_mcts_budget()
    refresh, refresh_search = summarize_refresh_rule()
    spread_raw, spread_summary, spread_search = summarize_spread_goals()
    feasibility = summarize_expectimax_feasibility()
    net_usage = summarize_net_usage()

    fast_results.to_csv(TABLES / "06_all_fast_results.csv", index=False)
    rule_greedy.to_csv(TABLES / "01_fast_rule_greedy.csv", index=False, float_format="%.6f")
    deadlocks.to_csv(TABLES / "02_deadlocks.csv", index=False, float_format="%.6f")
    search_summary.to_csv(TABLES / "03_search_factors.csv", index=False, float_format="%.6f")
    expectimax.to_csv(TABLES / "04_expectimax_depth.csv", index=False, float_format="%.6f")
    mcts.to_csv(TABLES / "05_mcts_budget.csv", index=False, float_format="%.6f")
    search_results.to_csv(TABLES / "07_all_search_results.csv", index=False)
    refresh.to_csv(TABLES / "08_refresh_rule_comparison.csv", index=False, float_format="%.6f")
    refresh_search.to_csv(TABLES / "09_refresh_search_comparison.csv", index=False, float_format="%.6f")
    spread_raw.to_csv(TABLES / "10_spread_point_goal_results.csv", index=False)
    spread_summary.to_csv(TABLES / "11_spread_point_goal_summary.csv", index=False, float_format="%.6f")
    spread_search.to_csv(TABLES / "12_spread_search_agents.csv", index=False, float_format="%.6f")
    net_usage.to_csv(TABLES / "13_net_launcher_usage.csv", index=False, float_format="%.6f")
    feasibility.to_csv(TABLES / "14_expectimax_depth_2_to_6.csv", index=False, float_format="%.6f")

    plot_boards()
    plot_rule_greedy(rule_greedy)
    plot_deadlocks(deadlocks)
    plot_search_family(search_summary, "Board", "04_search_agents_boards.png")
    plot_search_family(search_summary, "Pieces", "05_search_agents_pieces.png")
    plot_search_family(search_summary, "Deck", "05b_search_agents_decks.png")
    plot_expectimax_budget(expectimax)
    plot_mcts_budget(mcts)
    plot_refresh_rule(refresh, refresh_search)
    plot_spread_boards()
    plot_point_goals(spread_summary, spread_search)
    plot_expectimax_feasibility(feasibility)
    plot_net_usage(net_usage)
    write_analysis(
        fast_results,
        rule_greedy,
        deadlocks,
        search_summary,
        expectimax,
        mcts,
        refresh,
        refresh_search,
        spread_summary,
        spread_search,
        feasibility,
        net_usage,
    )
    write_indexes()
    print(f"Wrote {OUT}")
    print(f"New games analyzed: {len(fast_results) + len(search_results) + 6 * 12 + 114 + 234}")


if __name__ == "__main__":
    main()
