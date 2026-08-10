"""Analyze the corrected public-information reduced-factorial matrix."""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "final_results" / "corrected_factorial"
FIGURES = OUT / "figures"
TABLES = OUT / "tables"
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".mplconfig"))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


AGENTS = ["random", "greedy", "rule", "expectimax_d2", "expectimax_d3", "mcts"]
AGENT_LABELS = {
    "random": "Random",
    "greedy": "Greedy",
    "rule": "Rule",
    "expectimax_d2": "Expectimax d2",
    "expectimax_d3": "Expectimax d3",
    "expectimax_d4": "Expectimax d4",
    "mcts": "MCTS",
}
COLORS = {
    "random": "#9c9c9c",
    "greedy": "#4e79a7",
    "rule": "#59a14f",
    "expectimax_d2": "#f28e2b",
    "expectimax_d3": "#e15759",
    "expectimax_d4": "#b07aa1",
    "mcts": "#76b7b2",
}

BOARD_MODES = {
    "corrected_reduced_board_default_fixed_r2": ("Default", "Fixed 25"),
    "corrected_reduced_board_default_goal10_r2": ("Default", "Goal 10"),
    "corrected_reduced_board_default_goal40_r2": ("Default", "Goal 40"),
    "corrected_reduced_board_bottleneck_7x7_fixed_r2": ("Bottleneck 7x7", "Fixed 25"),
    "corrected_reduced_board_bottleneck_7x7_goal10_r2": ("Bottleneck 7x7", "Goal 10"),
    "corrected_reduced_board_bottleneck_7x7_goal40_r2": ("Bottleneck 7x7", "Goal 40"),
    "corrected_reduced_board_inner_ring_center_7x7_fixed_r2": ("Inner ring", "Fixed 25"),
    "corrected_reduced_board_inner_ring_center_7x7_goal10_r2": ("Inner ring", "Goal 10"),
    "corrected_reduced_board_inner_ring_center_7x7_goal40_r2": ("Inner ring", "Goal 40"),
}
DECK_MODES = {
    "corrected_reduced_board_default_fixed_r2": "Default",
    "corrected_reduced_deck_movement_heavy_fixed_r2": "Movement-heavy",
    "corrected_reduced_deck_capture_heavy_fixed_r2": "Capture-heavy",
    "corrected_reduced_deck_swap_heavy_fixed_r2": "Swap-heavy",
}
DEPTH_MODES = {
    "corrected_reduced_depth_default_goal20_r2": "Default",
    "corrected_reduced_depth_bottleneck_7x7_goal20_r2": "Bottleneck 7x7",
    "corrected_reduced_depth_inner_ring_center_7x7_goal20_r2": "Inner ring",
}
ALL_MODES = list(BOARD_MODES) + [
    mode for mode in DECK_MODES if mode not in BOARD_MODES
] + list(DEPTH_MODES)


def mode_config(mode: str) -> dict:
    return json.loads((ROOT / "modes" / mode / "config.json").read_text(encoding="utf-8"))


def load_results(mode: str) -> pd.DataFrame:
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
        for side, seat, agent, opponent, score, other, time_value, decisions, turns in (
            (
                "A", "first", row.agent_a, row.agent_b, row.score_a, row.score_b,
                row.decision_time_a_seconds, row.decisions_a, row.turns_a,
            ),
            (
                "B", "second", row.agent_b, row.agent_a, row.score_b, row.score_a,
                row.decision_time_b_seconds, row.decisions_b, row.turns_b,
            ),
        ):
            rows.append(
                {
                    "mode": row.mode,
                    "pair": row.pair,
                    "game": int(row.game),
                    "agent": agent,
                    "opponent": opponent,
                    "seat": seat,
                    "outcome": 1.0 if row.winner == side else 0.5 if row.winner == "draw" else 0.0,
                    "score": int(score),
                    "margin": int(score) - int(other),
                    "decision_time_seconds": float(time_value),
                    "decisions": int(decisions),
                    "turns": int(turns),
                }
            )
    data = pd.DataFrame(rows)
    data["milliseconds_per_decision"] = (
        1000 * data.decision_time_seconds / data.decisions.replace(0, np.nan)
    )
    return data


def validate_coverage() -> pd.DataFrame:
    rows = []
    for mode in ALL_MODES:
        config = mode_config(mode)
        expected_pairs = 12 if mode in DEPTH_MODES else 30
        expected_games_per_pair = 1 if mode in DEPTH_MODES else 3
        result_files = sorted((ROOT / "modes" / mode / "results").glob("*.csv"))
        game_files = sorted((ROOT / "modes" / mode / "games").glob("*/*.csv"))
        results = load_results(mode)
        pair_sizes = results.groupby("pair").size() if not results.empty else pd.Series(dtype=int)
        passed = (
            config["rules"].get("market_refresh_after_passes") == 2
            and len(result_files) == expected_pairs
            and len(game_files) == expected_pairs * expected_games_per_pair
            and len(results) == expected_pairs * expected_games_per_pair
            and not pair_sizes.empty
            and pair_sizes.eq(expected_games_per_pair).all()
        )
        rows.append(
            {
                "mode": mode,
                "board": config["board"]["name"],
                "deck": config["deck"]["name"],
                "turns_per_player": config["rules"]["turns_per_player"],
                "score_to_win": config["rules"].get("score_to_win"),
                "market_refresh_after_passes": config["rules"].get("market_refresh_after_passes"),
                "agents": ",".join(entry["name"] for entry in config["agents"]),
                "expected_pairs": expected_pairs,
                "result_pair_files": len(result_files),
                "expected_games": expected_pairs * expected_games_per_pair,
                "result_rows": len(results),
                "game_logs": len(game_files),
                "coverage_ok": passed,
            }
        )
    coverage = pd.DataFrame(rows)
    if not coverage.coverage_ok.all():
        raise ValueError(f"Incomplete coverage:\n{coverage[~coverage.coverage_ok]}")
    return coverage


def aggregate_agents(long: pd.DataFrame, group_fields: list[str]) -> pd.DataFrame:
    summary = (
        long.groupby(group_fields + ["agent"], as_index=False)
        .agg(
            games=("outcome", "size"),
            win_points_rate=("outcome", "mean"),
            mean_margin=("margin", "mean"),
            mean_score=("score", "mean"),
            total_decision_time=("decision_time_seconds", "sum"),
            total_decisions=("decisions", "sum"),
            mean_turns=("turns", "mean"),
        )
    )
    summary["milliseconds_per_decision"] = (
        1000 * summary.total_decision_time / summary.total_decisions
    )
    return summary


def extract_net_usage(modes: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    events = []
    for mode in modes:
        for path in sorted((ROOT / "modes" / mode / "games").glob("*/*.csv")):
            pair = path.parent.name
            result_path = ROOT / "modes" / mode / "results" / f"{pair}.csv"
            result_rows = pd.read_csv(result_path)
            game_result = result_rows[result_rows.game == int(path.stem)].iloc[0]
            agent_a, agent_b = game_result.agent_a, game_result.agent_b
            with path.open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            # Each row's action fields describe the PREVIOUS turn's move; the
            # played card is the previous row's card_<action> slot (card_drawn
            # is the replacement drawn afterwards).
            for prev, row in zip(rows, rows[1:]):
                slot = row["action"]
                if slot in ("-1", "", "None"):
                    continue
                if prev[f"card_{slot}"] != "capture":
                    continue
                mover = 1 - int(row["player"])
                events.append(
                    {
                        "mode": mode,
                        "agent": agent_a if mover == 0 else agent_b,
                        "capture_type": (
                            "net" if row["src_1"] not in ("", "-1", "None") else "adjacent"
                        ),
                    }
                )
    raw = pd.DataFrame(events)
    counts = raw.groupby(["agent", "capture_type"]).size().unstack(fill_value=0)
    for column in ("adjacent", "net"):
        if column not in counts:
            counts[column] = 0
    counts = counts.reset_index()
    counts["total_captures"] = counts.adjacent + counts.net
    counts["net_share"] = counts.net / counts.total_captures
    return raw, counts.sort_values("agent")


def extract_action_usage(modes: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Reconstruct played card types from trailing previous-action log fields."""
    cards = ["move1", "move2", "mobilize", "capture", "swap"]
    events = []
    for mode in modes:
        for path in sorted((ROOT / "modes" / mode / "games").glob("*/*.csv")):
            pair = path.parent.name
            result_rows = pd.read_csv(ROOT / "modes" / mode / "results" / f"{pair}.csv")
            game_result = result_rows[result_rows.game == int(path.stem)].iloc[0]
            agent_a, agent_b = game_result.agent_a, game_result.agent_b
            with path.open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            # Played card = previous row's card_<action>; see extract_net_usage.
            for prev, row in zip(rows, rows[1:]):
                slot = row["action"]
                if slot in ("-1", "", "None"):
                    continue
                card = prev[f"card_{slot}"]
                if card not in cards:
                    continue
                mover = 1 - int(row["player"])
                events.append({
                    "mode": mode,
                    "agent": agent_a if mover == 0 else agent_b,
                    "card": card,
                })
    raw = pd.DataFrame(events)
    counts = raw.groupby(["agent", "card"]).size().unstack(fill_value=0)
    for card in cards:
        if card not in counts:
            counts[card] = 0
    counts = counts[cards].reset_index()
    counts["played_actions"] = counts[cards].sum(axis=1)
    for card in cards:
        counts[f"{card}_share"] = counts[card] / counts.played_actions
    counts["most_used_card"] = counts[cards].idxmax(axis=1)
    counts["most_used_share"] = counts[[f"{card}_share" for card in cards]].max(axis=1)
    return raw, counts.sort_values("agent")


def plot_grouped(data: pd.DataFrame, x_field: str, filename: str, title: str) -> None:
    conditions = list(dict.fromkeys(data[x_field]))
    fig, ax = plt.subplots(figsize=(13, 6))
    x = np.arange(len(conditions))
    width = 0.13
    for index, agent in enumerate(AGENTS):
        values = (
            data[data.agent == agent].set_index(x_field)
            .reindex(conditions).win_points_rate.mul(100)
        )
        ax.bar(
            x + (index - 2.5) * width, values, width,
            label=AGENT_LABELS[agent], color=COLORS[agent],
        )
    ax.axhline(50, color="#333333", linestyle="--", linewidth=1)
    ax.set_xticks(x, conditions)
    ax.set_ylabel("Win points across five opponents (%)")
    ax.set_title(title, loc="left", fontweight="bold")
    ax.legend(frameon=False, ncol=3)
    ax.grid(axis="y", alpha=0.25)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(FIGURES / filename, dpi=220, bbox_inches="tight")
    plt.close(fig)


def create_outputs() -> dict[str, pd.DataFrame]:
    FIGURES.mkdir(parents=True, exist_ok=True)
    TABLES.mkdir(parents=True, exist_ok=True)
    coverage = validate_coverage()

    board_results = pd.concat([load_results(mode) for mode in BOARD_MODES], ignore_index=True)
    board_long = to_long(board_results)
    board_meta = pd.DataFrame(
        [{"mode": mode, "board": board, "end_condition": end} for mode, (board, end) in BOARD_MODES.items()]
    )
    board_long = board_long.merge(board_meta, on="mode")
    board_long["condition"] = board_long.board + "\n" + board_long.end_condition
    board_summary = aggregate_agents(board_long, ["mode", "board", "end_condition", "condition"])

    deck_results = pd.concat([load_results(mode) for mode in DECK_MODES], ignore_index=True)
    deck_long = to_long(deck_results)
    deck_meta = pd.DataFrame([{"mode": mode, "deck": deck} for mode, deck in DECK_MODES.items()])
    deck_long = deck_long.merge(deck_meta, on="mode")
    deck_summary = aggregate_agents(deck_long, ["mode", "deck"])

    main_unique_modes = list(BOARD_MODES) + [m for m in DECK_MODES if m not in BOARD_MODES]
    main_results = pd.concat([load_results(mode) for mode in main_unique_modes], ignore_index=True)
    main_long = to_long(main_results)
    seat_summary = aggregate_agents(main_long, ["seat"])

    depth_results = pd.concat([load_results(mode) for mode in DEPTH_MODES], ignore_index=True)
    depth_long = to_long(depth_results)
    depth_meta = pd.DataFrame([{"mode": mode, "board": board} for mode, board in DEPTH_MODES.items()])
    depth_long = depth_long.merge(depth_meta, on="mode")
    depth_summary = aggregate_agents(depth_long, ["mode", "board"])

    direct_rows = []
    for mode, (board, end) in BOARD_MODES.items():
        data = to_long(load_results(mode))
        direct = data[
            data.agent.isin(["expectimax_d2", "expectimax_d3"])
            & data.opponent.isin(["expectimax_d2", "expectimax_d3"])
        ]
        for agent, subset in direct.groupby("agent"):
            direct_rows.append(
                {
                    "mode": mode,
                    "board": board,
                    "end_condition": end,
                    "agent": agent,
                    "games": len(subset),
                    "win_points_rate": subset.outcome.mean(),
                    "mean_margin": subset.margin.mean(),
                    "milliseconds_per_decision": (
                        1000 * subset.decision_time_seconds.sum() / subset.decisions.sum()
                    ),
                }
            )
    direct_depth = pd.DataFrame(direct_rows)

    board_game_summary = (
        board_results.merge(board_meta, on="mode")
        .assign(
            total_turns=lambda x: x.turns_a + x.turns_b,
            total_score=lambda x: x.score_a + x.score_b,
            draw=lambda x: x.winner.eq("draw"),
        )
        .groupby(["mode", "board", "end_condition"], as_index=False)
        .agg(
            games=("game", "size"),
            draw_rate=("draw", "mean"),
            mean_total_turns=("total_turns", "mean"),
            mean_total_score=("total_score", "mean"),
        )
    )

    net_raw, net_summary = extract_net_usage(main_unique_modes + list(DEPTH_MODES))

    coverage.to_csv(TABLES / "01_coverage_manifest.csv", index=False)
    board_summary.to_csv(TABLES / "02_board_goal_agent_performance.csv", index=False, float_format="%.6f")
    seat_summary.to_csv(TABLES / "03_agent_order.csv", index=False, float_format="%.6f")
    deck_summary.to_csv(TABLES / "04_deck_agent_performance.csv", index=False, float_format="%.6f")
    direct_depth.to_csv(TABLES / "05_expectimax_d2_vs_d3.csv", index=False, float_format="%.6f")
    depth_summary.to_csv(TABLES / "06_bounded_depth_performance.csv", index=False, float_format="%.6f")
    net_summary.to_csv(TABLES / "07_net_launcher_usage.csv", index=False, float_format="%.6f")
    net_raw.to_csv(TABLES / "08_net_capture_events.csv", index=False)
    board_game_summary.to_csv(TABLES / "09_board_goal_game_length.csv", index=False, float_format="%.6f")
    main_results.to_csv(TABLES / "10_all_main_results.csv", index=False)
    depth_results.to_csv(TABLES / "11_all_bounded_depth_results.csv", index=False)

    plot_grouped(
        board_summary, "condition", "01_board_goal_performance.png",
        "Agent performance across three boards and two end conditions",
    )
    plot_grouped(
        deck_summary, "deck", "03_deck_performance.png",
        "Independent deck-composition test on the default board",
    )

    seat_pivot = seat_summary.pivot(index="agent", columns="seat", values="win_points_rate").loc[AGENTS]
    fig, ax = plt.subplots(figsize=(9, 5.2))
    x = np.arange(len(AGENTS))
    ax.bar(x - 0.18, seat_pivot["first"] * 100, 0.36, label="First", color="#4e79a7")
    ax.bar(x + 0.18, seat_pivot["second"] * 100, 0.36, label="Second", color="#f28e2b")
    ax.set_xticks(x, [AGENT_LABELS[a] for a in AGENTS], rotation=20, ha="right")
    ax.set_ylabel("Win points (%)")
    ax.set_title("Going first versus going second across the reduced main suite", loc="left", fontweight="bold")
    ax.legend(frameon=False)
    ax.grid(axis="y", alpha=0.25)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(FIGURES / "02_agent_order.png", dpi=220, bbox_inches="tight")
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(12, 5.2))
    direct_plot = direct_depth.copy()
    direct_plot["condition"] = direct_plot.board + "\n" + direct_plot.end_condition
    conditions = list(dict.fromkeys(direct_plot.condition))
    x = np.arange(len(conditions))
    for offset, agent in ((-0.18, "expectimax_d2"), (0.18, "expectimax_d3")):
        subset = direct_plot[direct_plot.agent == agent].set_index("condition").loc[conditions]
        axes[0].bar(x + offset, subset.win_points_rate * 100, 0.36, label=AGENT_LABELS[agent], color=COLORS[agent])
    axes[0].axhline(50, color="#333333", linestyle="--", linewidth=1)
    axes[0].set_xticks(x, conditions, rotation=25, ha="right")
    axes[0].set_ylabel("Direct head-to-head win points (%)")
    axes[0].set_title("Depth 2 versus depth 3", loc="left", fontweight="bold")
    bounded = depth_summary[depth_summary.agent.str.startswith("expectimax")].copy()
    for agent in ("expectimax_d2", "expectimax_d3", "expectimax_d4"):
        subset = bounded[bounded.agent == agent].set_index("board").reindex(list(DEPTH_MODES.values()))
        axes[1].plot(
            list(DEPTH_MODES.values()), subset.milliseconds_per_decision,
            marker="o", linewidth=2, label=AGENT_LABELS[agent], color=COLORS[agent],
        )
    axes[1].set_yscale("log")
    axes[1].set_ylabel("Weighted mean ms/decision (log scale)")
    axes[1].set_title("Bounded depth cost", loc="left", fontweight="bold")
    for ax in axes:
        ax.legend(frameon=False)
        ax.grid(axis="y", alpha=0.25)
        ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(FIGURES / "04_expectimax_depths.png", dpi=220, bbox_inches="tight")
    plt.close(fig)

    overall = aggregate_agents(main_long, [])
    fig, ax = plt.subplots(figsize=(8.5, 5.4))
    for row in overall.itertuples(index=False):
        ax.scatter(
            row.milliseconds_per_decision, row.win_points_rate * 100,
            s=95, color=COLORS[row.agent], label=AGENT_LABELS[row.agent],
        )
        ax.annotate(AGENT_LABELS[row.agent], (row.milliseconds_per_decision, row.win_points_rate * 100), xytext=(5, 4), textcoords="offset points")
    ax.set_xscale("log")
    ax.set_xlabel("Weighted mean ms/decision (log scale)")
    ax.set_ylabel("Win points across reduced main suite (%)")
    ax.set_title("Performance versus decision cost", loc="left", fontweight="bold")
    ax.grid(alpha=0.25)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(FIGURES / "05_runtime_performance.png", dpi=220, bbox_inches="tight")
    plt.close(fig)

    net_plot = net_summary.set_index("agent").reindex([a for a in AGENTS if a in set(net_summary.agent)]).reset_index()
    fig, ax = plt.subplots(figsize=(9, 5.4))
    x = np.arange(len(net_plot))
    ax.bar(x, net_plot.adjacent, label="Adjacent", color="#76b7b2")
    ax.bar(x, net_plot.net, bottom=net_plot.adjacent, label="Net launcher", color="#f28e2b")
    for index, row in enumerate(net_plot.itertuples(index=False)):
        ax.text(index, row.total_captures + 2, f"{row.net_share:.0%} net", ha="center", fontsize=9)
    ax.set_xticks(x, [AGENT_LABELS[a] for a in net_plot.agent], rotation=15, ha="right")
    ax.set_ylabel("Capture actions")
    ax.set_title("Adjacent and net-launcher captures in the completed suite", loc="left", fontweight="bold")
    ax.legend(frameon=False)
    ax.grid(axis="y", alpha=0.25)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(FIGURES / "06_net_launcher_usage.png", dpi=220, bbox_inches="tight")
    plt.close(fig)

    return {
        "coverage": coverage,
        "board_summary": board_summary,
        "seat_summary": seat_summary,
        "deck_summary": deck_summary,
        "direct_depth": direct_depth,
        "depth_summary": depth_summary,
        "net_summary": net_summary,
        "board_game_summary": board_game_summary,
        "overall": overall,
    }


def write_report(data: dict[str, pd.DataFrame]) -> None:
    overall = data["overall"].sort_values("win_points_rate", ascending=False)
    best = overall.iloc[0]
    seats = data["seat_summary"].pivot(index="agent", columns="seat", values="win_points_rate")
    seat_delta = (seats["first"] - seats["second"]).sort_values(ascending=False)
    direct = data["direct_depth"]
    d3 = direct[direct.agent == "expectimax_d3"]
    d3_games = int(d3.games.sum())
    d3_points = float((d3.win_points_rate * d3.games).sum() / d3.games.sum())
    net = data["net_summary"]
    net_total = int(net.net.sum())
    capture_total = int(net.total_captures.sum())
    lengths = data["board_game_summary"]
    goal10_turns = lengths[lengths.end_condition == "Goal 10"].mean_total_turns.mean()
    goal40_turns = lengths[lengths.end_condition == "Goal 40"].mean_total_turns.mean()
    fixed_turns = lengths[lengths.end_condition == "Fixed 25"].mean_total_turns.mean()

    text = f"""# Reduced factorial experiment report

## Design and coverage

The completed suite contains **1,116 games**:

- 810 games crossing three boards (default, bottleneck 7x7, inner-ring center) with fixed 25-turn, first-to-10, and first-to-40 end conditions;
- 270 independent deck games on the default board (movement-heavy, capture-heavy, swap-heavy; the default-deck control is shared with the board suite);
- 36 bounded first-to-20 games directly comparing rule and expectimax depths 2, 3, and 4.

Every main/deck condition contains six agents, all 30 ordered non-self pairs, three matched seeds, and the two-consecutive-pass market refresh. The coverage manifest verifies all result rows and per-game logs. Depths 2 and 3 use the same top-2 action cap and play each other directly. Depth 4 is bounded to one seed; depths 5-6 remain computationally infeasible.

## Main performance

Across the 12 unique main/deck modes, **{AGENT_LABELS[best.agent]}** has the highest aggregate win-points rate ({best.win_points_rate:.1%}). Figure 01 shows that rankings depend on board and end condition; Figure 03 isolates deck composition.

These are screening estimates: each agent has 30 games per condition, but each direct matchup has only six games. Interpret large reversals, not small percentage differences.

## Agent order

All matchups use identical seeds in both orientations. The largest aggregate first-seat advantage is for **{AGENT_LABELS[seat_delta.index[0]]}** at {seat_delta.iloc[0]:+.1%} win points; the smallest (or most negative) is **{AGENT_LABELS[seat_delta.index[-1]]}** at {seat_delta.iloc[-1]:+.1%}. Figure 02 and Table 03 provide every agent's first/second split.

## Boards and point goal

The first-to-10 condition ended after {goal10_turns:.1f} combined turns on average across boards; first-to-40 ended after {goal40_turns:.1f}, versus {fixed_turns:.1f} scheduled turns under the 25-turn-per-player condition. This changes both strategy and compute cost, so goal-based and fixed-horizon results should be reported separately rather than pooled as interchangeable replications.

The inner-ring single-center board is the concentrated-objective condition: its +4 center reward exceeds the default +3 capture reward, making rushing and holding the center locally more valuable than one capture.

## Deck composition

Deck composition is tested independently on the default board with a fixed 25-turn horizon. This avoids confusing deck effects with board geometry or early stopping. All deck modes use the refreshed market, so the earlier absorbing capture-heavy market no longer contaminates the comparison.

## Expectimax depth

Across the six board/end direct comparisons, depth 3 receives {d3_points:.1%} of win points against depth 2 over {d3_games} agent-game observations. The result varies by condition and is not monotonic evidence that deeper is always stronger.

The bounded depth study shows the computational jump through depth 4 on all three boards. Depth 4 has only six games per board across three opponents and should be treated as timing/feasibility evidence, not a stable strength estimate.

## Net launcher

Across the full completed suite, {net_total} of {capture_total} captures ({net_total / capture_total:.1%}) use the net launcher. Figure 06 and Table 07 report both counts and shares by agent. Counts matter alongside percentages because agents differ substantially in total capture frequency.

## Reproduction

```powershell
python analysis/reduced_factorial_report.py
```
"""
    (OUT / "01_ANALYSIS.md").write_text(text, encoding="utf-8")

    files = [
        ("01_ANALYSIS.md", "Interpretation and limitations"),
        ("figures/01_board_goal_performance.png", "Agent performance by board and end condition"),
        ("figures/02_agent_order.png", "First-versus-second comparison"),
        ("figures/03_deck_performance.png", "Independent deck-composition results"),
        ("figures/04_expectimax_depths.png", "Direct depth comparison and bounded runtime"),
        ("figures/05_runtime_performance.png", "Performance-runtime trade-off"),
        ("figures/06_net_launcher_usage.png", "Adjacent versus net captures"),
        ("tables/01_coverage_manifest.csv", "Proof of complete planned coverage"),
        ("tables/02_board_goal_agent_performance.csv", "Board/end-condition agent results"),
        ("tables/03_agent_order.csv", "First and second seat results"),
        ("tables/04_deck_agent_performance.csv", "Independent deck results"),
        ("tables/05_expectimax_d2_vs_d3.csv", "Direct depth-2 versus depth-3 results"),
        ("tables/06_bounded_depth_performance.csv", "Depths 2-4 bounded comparison"),
        ("tables/07_net_launcher_usage.csv", "Net usage by agent"),
        ("tables/08_net_capture_events.csv", "Capture-event source data"),
        ("tables/09_board_goal_game_length.csv", "Game length and score by end condition"),
        ("tables/10_all_main_results.csv", "All 810 main/deck result rows"),
        ("tables/11_all_bounded_depth_results.csv", "All 36 bounded depth rows"),
        ("../../analysis/reduced_factorial_report.py", "Reproduction script"),
        ("../../analysis/validate_reduced_factorial.py", "Full replay validator"),
    ]
    links = "\n".join(f"- [{path}]({path}) — {description}" for path, description in files)
    index = f"""# Reduced factorial results

Start with [01_ANALYSIS.md](01_ANALYSIS.md). The suite contains 1,116 games, uses the two-pass market refresh throughout, compares every planned ordered pair, and includes net-launcher statistics.

## Files

{links}
"""
    (OUT / "00_INDEX.md").write_text(index, encoding="utf-8")


def main() -> None:
    data = create_outputs()
    write_report(data)
    print(f"Wrote {OUT}")
    print(f"Coverage rows: {len(data['coverage'])}; all valid: {data['coverage'].coverage_ok.all()}")
    print("Games analyzed: 1116")


if __name__ == "__main__":
    main()
