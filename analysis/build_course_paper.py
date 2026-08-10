"""Build the course-format Graph Card Control paper and its figures.

The PDF uses an AAAI-like US-Letter, two-column layout because the course
guidelines recommend AAAI '27 camera-ready formatting. Each figure is built
from replay-validated corrected data and exported as PNG and vector PDF.
"""

from __future__ import annotations

import csv
import json
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

OUT = ROOT / "final_results" / "course_paper"
FIG_DIR = OUT / "figures"
TABLE_DIR = OUT / "tables"
PDF_DIR = ROOT / "output" / "pdf"
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".mplconfig"))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Rectangle
import numpy as np
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    BalancedColumns, BaseDocTemplate, Frame, FrameBreak, Image, KeepTogether,
    NextPageTemplate, PageBreak, PageTemplate, Paragraph, Spacer, Table, TableStyle,
)

from build_final_report import prepare_data
from reduced_factorial_report import AGENTS, AGENT_LABELS, COLORS


AGENT_ORDER = ["rule", "mcts", "expectimax_d3", "expectimax_d2", "greedy", "random"]
BOARD_ORDER = ["Default", "Bottleneck 7x7", "Inner ring"]
END_ORDER = ["Fixed 25", "Goal 10", "Goal 40"]
DECK_ORDER = ["Default", "Movement-heavy", "Capture-heavy", "Swap-heavy"]
DECK_COUNTS = {
    "Default": [8, 6, 5, 5, 4],
    "Movement-heavy": [10, 8, 6, 2, 2],
    "Capture-heavy": [5, 4, 4, 11, 4],
    "Swap-heavy": [6, 5, 4, 4, 9],
}
CARD_LABELS = ["Move 1", "Move 2", "Mobilize", "Capture", "Swap"]
CARD_COLORS = ["#4E79A7", "#76B7B2", "#59A14F", "#F28E2B", "#B07AA1"]


def configure_plotting() -> None:
    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "font.size": 7.3,
        "axes.titlesize": 8.4,
        "axes.labelsize": 7.3,
        "xtick.labelsize": 6.8,
        "ytick.labelsize": 6.8,
        "legend.fontsize": 6.7,
        "axes.linewidth": 0.7,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    })


def export_figure(fig: plt.Figure, stem: str) -> Path:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    png = FIG_DIR / f"{stem}.png"
    pdf = FIG_DIR / f"{stem}.pdf"
    fig.savefig(png, dpi=300, bbox_inches="tight", pad_inches=0.035, facecolor="white")
    fig.savefig(pdf, bbox_inches="tight", pad_inches=0.035, facecolor="white")
    plt.close(fig)
    return png


def panel_label(ax: plt.Axes, label: str) -> None:
    ax.text(-0.12, 1.04, label, transform=ax.transAxes, fontsize=9.5,
            fontweight="bold", ha="left", va="bottom", clip_on=False)


def clean_axis(ax: plt.Axes, grid: str | None = "y") -> None:
    ax.spines[["top", "right"]].set_visible(False)
    if grid:
        ax.grid(axis=grid, color="#B8C0C8", linewidth=0.45, alpha=0.45)
        ax.set_axisbelow(True)


def draw_board(ax: plt.Axes, board: dict, title: str) -> None:
    rows, cols = board["rows"], board["cols"]
    ax.set_xlim(-0.52, cols - 0.48)
    ax.set_ylim(rows - 0.48, -0.52)
    ax.set_aspect("equal")
    ax.set_xticks(np.arange(-0.5, cols, 1), minor=True)
    ax.set_yticks(np.arange(-0.5, rows, 1), minor=True)
    ax.grid(which="minor", color="#AEB6BE", linewidth=0.55)
    ax.set_xticks([]); ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
    for r, c in board.get("blocked_cells", []):
        ax.add_patch(Rectangle((c - .47, r - .47), .94, .94,
                               facecolor="#3E454B", edgecolor="none", zorder=2))
    for entry in board["capture_cells"]:
        r, c = entry["cell"]
        ax.add_patch(Rectangle((c - .43, r - .43), .86, .86,
                               facecolor="#F2CF5B", edgecolor="#A77800", linewidth=.65, zorder=3))
        ax.text(c, r, f"+{entry['points']}", ha="center", va="center",
                fontsize=6.7, fontweight="bold", color="#4A3600", zorder=4)
    for player, color in (("A", "#4E79A7"), ("B", "#E15759")):
        for r, c in board["spawns"][player]:
            ax.add_patch(Circle((c, r), .28, facecolor=color, edgecolor="white", linewidth=.55, zorder=5))
            ax.text(c, r, player, color="white", ha="center", va="center",
                    fontsize=6.3, fontweight="bold", zorder=6)
    ax.set_title(title, fontweight="bold", pad=2.5)


def figure_1_mechanics() -> Path:
    """Principal claim: the rules isolate one stochastic event within a transparent turn."""
    fig = plt.figure(figsize=(7.05, 2.48))
    gs = fig.add_gridspec(1, 3, width_ratios=[1.08, 1.0, 1.08], wspace=.23)

    ax = fig.add_subplot(gs[0, 0]); ax.axis("off"); panel_label(ax, "A")
    ax.set_title("Turn sequence", loc="left", fontweight="bold", pad=4)
    steps = [
        ("1", "Select", "one public card"),
        ("2", "Act", "legal move only"),
        ("3", "Score", "+3 capture; objective"),
        ("4", "Refill", "random card draw"),
        ("5", "Stop?", "horizon or point goal"),
    ]
    ys = np.linspace(.84, .18, len(steps))
    for i, (num, head, detail) in enumerate(steps):
        box = FancyBboxPatch((.06, ys[i] - .06), .86, .115,
                             boxstyle="round,pad=.008,rounding_size=.018",
                             facecolor="#F2F5F7", edgecolor="#5B7690", linewidth=.7,
                             transform=ax.transAxes)
        ax.add_patch(box)
        ax.text(.105, ys[i], num, transform=ax.transAxes, ha="center", va="center",
                fontsize=7.2, fontweight="bold", color="#315E7D")
        ax.text(.19, ys[i] + .018, head, transform=ax.transAxes, ha="left", va="center",
                fontsize=7.1, fontweight="bold")
        ax.text(.19, ys[i] - .025, detail, transform=ax.transAxes, ha="left", va="center",
                fontsize=5.9, color="#3F474E")
        if i < len(steps) - 1:
            ax.add_patch(FancyArrowPatch((.49, ys[i] - .065), (.49, ys[i + 1] + .065),
                                         transform=ax.transAxes, arrowstyle="-|>",
                                         mutation_scale=7, linewidth=.55, color="#6B737A"))
    ax.text(.49, .025, "No legal card: pass; two passes: refresh market",
            transform=ax.transAxes, ha="center", va="bottom", fontsize=5.7, color="#7A3E00")

    ax = fig.add_subplot(gs[0, 1]); ax.axis("off"); panel_label(ax, "B")
    ax.set_title("Action cards", loc="left", fontweight="bold", pad=4)
    rows = [
        ("Move 1", "one piece, 1 step"),
        ("Move 2", "one piece, up to 2"),
        ("Mobilize", "two pieces, 1 each"),
        ("Capture", "adjacent or net ray"),
        ("Swap", "enemy within range 3"),
    ]
    for i, ((name, detail), color) in enumerate(zip(rows, CARD_COLORS)):
        y = .84 - i * .155
        ax.add_patch(Rectangle((.04, y - .05), .055, .1, transform=ax.transAxes,
                               facecolor=color, edgecolor="none"))
        ax.text(.13, y + .017, name, transform=ax.transAxes, fontsize=7.0,
                fontweight="bold", va="center")
        ax.text(.13, y - .028, detail, transform=ax.transAxes, fontsize=6.0,
                color="#3F474E", va="center")
        ax.plot([.04, .94], [y - .077, y - .077], transform=ax.transAxes,
                color="#D7DDE2", linewidth=.45)
    ax.text(.04, .035, "Market size = 3; default deck = 28 cards",
            transform=ax.transAxes, fontsize=5.9, color="#3F474E")

    ax = fig.add_subplot(gs[0, 2]); ax.axis("off"); panel_label(ax, "C")
    ax.set_title("Two capture modes", loc="left", fontweight="bold", pad=4)

    # Regular capture: the friendly piece is orthogonally adjacent to its target.
    regular = FancyBboxPatch((.055, .63), .89, .26,
                             boxstyle="round,pad=.008,rounding_size=.018",
                             facecolor="#F7F9FA", edgecolor="#7E8A93", linewidth=.65,
                             transform=ax.transAxes)
    ax.add_patch(regular)
    ax.text(.085, .855, "Regular capture", transform=ax.transAxes,
            ha="left", va="top", fontsize=6.5, fontweight="bold")
    regular_y = .735
    for x in (.39, .55):
        ax.add_patch(Rectangle((x - .065, regular_y - .065), .13, .13,
                               transform=ax.transAxes, facecolor="white",
                               edgecolor="#AAB2B9", linewidth=.55))
    ax.add_patch(Circle((.39, regular_y), .043, transform=ax.transAxes,
                        facecolor="#4E79A7", edgecolor="white", linewidth=.5))
    ax.add_patch(Circle((.55, regular_y), .043, transform=ax.transAxes,
                        facecolor="#E15759", edgecolor="white", linewidth=.5))
    ax.add_patch(FancyArrowPatch((.43, regular_y), (.505, regular_y),
                                 transform=ax.transAxes, arrowstyle="-|>",
                                 mutation_scale=8, linewidth=1.0, color="#F28E2B"))
    ax.text(.73, regular_y, "adjacent\nenemy", transform=ax.transAxes,
            ha="center", va="center", fontsize=5.8, color="#3F474E")

    # Net-launcher schematic: preserve the former example and frame it explicitly.
    net = FancyBboxPatch((.055, .29), .89, .29,
                         boxstyle="round,pad=.008,rounding_size=.018",
                         facecolor="#FFF8EE", edgecolor="#D28A2B", linewidth=.75,
                         transform=ax.transAxes)
    ax.add_patch(net)
    ax.text(.085, .55, "Net launcher", transform=ax.transAxes,
            ha="left", va="top", fontsize=6.5, fontweight="bold", color="#9A5700")
    net_y = .425
    xs = [.14, .28, .42, .56, .70]
    for x in xs:
        ax.add_patch(Rectangle((x - .055, net_y - .055), .11, .11,
                               transform=ax.transAxes, facecolor="white",
                               edgecolor="#AAB2B9", linewidth=.5))
    for x in (.42, .56):
        ax.add_patch(Circle((x, net_y), .038, transform=ax.transAxes,
                            facecolor="#4E79A7", edgecolor="white", linewidth=.5))
    ax.add_patch(Circle((.14, net_y), .038, transform=ax.transAxes,
                        facecolor="#E15759", edgecolor="white", linewidth=.5))
    ax.add_patch(FancyArrowPatch((.385, net_y), (.185, net_y),
                                 transform=ax.transAxes, arrowstyle="-|>",
                                 mutation_scale=8, linewidth=1.0, color="#F28E2B"))
    ax.text(.82, net_y, "range 3", transform=ax.transAxes,
            ha="center", va="center", fontsize=5.6, color="#3F474E")
    ax.text(.50, .315, "friendly pair; first occupied stops ray",
            transform=ax.transAxes, ha="center", va="bottom", fontsize=5.05,
            color="#3F474E")

    # Shared scoring consequences.
    ax.text(.07, .205, "+3", transform=ax.transAxes, fontsize=7.0,
            fontweight="bold", color="#C46600", va="center")
    ax.text(.19, .205, "per capture; target respawns", transform=ax.transAxes,
            fontsize=5.8, va="center")
    ax.add_patch(Rectangle((.07, .085), .13, .09, transform=ax.transAxes,
                           facecolor="#F2CF5B", edgecolor="#A77800", linewidth=.6))
    ax.text(.135, .13, "+1/+4", transform=ax.transAxes, ha="center", va="center",
            fontsize=5.8, fontweight="bold")
    ax.text(.24, .13, "objective points at turn end", transform=ax.transAxes,
            ha="left", va="center", fontsize=5.7)
    ax.text(.07, .025, "Blue = acting side; red = captured target. Diagram is schematic.",
            transform=ax.transAxes, fontsize=5.45, color="#3F474E")

    return export_figure(fig, "01_game_mechanics")


def figure_2_boards() -> Path:
    """Principal claim: board geometry and objective value are controlled factors."""
    fig, axes = plt.subplots(1, 3, figsize=(7.05, 2.42))
    specs = [
        ("default", "Default 5x5", "open; center +1"),
        ("bottleneck_7x7", "Bottleneck 7x7", "blocked lanes; objectives +1/+3/+1"),
        ("inner_ring_center_7x7", "Inner-ring 7x7", "spread spawns; center +4"),
    ]
    for idx, (name, title, note) in enumerate(specs):
        board = json.loads((ROOT / "boards" / f"{name}.json").read_text(encoding="utf-8"))
        draw_board(axes[idx], board, title)
        panel_label(axes[idx], chr(ord("A") + idx))
        axes[idx].text(.5, -.075, note, transform=axes[idx].transAxes,
                       ha="center", va="top", fontsize=6.2, color="#3F474E")
    fig.subplots_adjust(left=.025, right=.995, top=.90, bottom=.14, wspace=.16)
    return export_figure(fig, "02_experimental_boards")


def annotated_heatmap(ax: plt.Axes, matrix: pd.DataFrame, title: str,
                      cmap: str = "RdYlBu", vmin: float = 0, vmax: float = 100,
                      fmt: str = ".0f") -> object:
    im = ax.imshow(matrix.to_numpy(), aspect="auto", cmap=cmap, vmin=vmin, vmax=vmax)
    midpoint = (vmin + vmax) / 2
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            value = float(matrix.iloc[i, j])
            ax.text(j, i, format(value, fmt), ha="center", va="center",
                    fontsize=6.1, fontweight="bold",
                    color="white" if abs(value - midpoint) > .31 * (vmax - vmin) else "#202428")
    ax.set_title(title, fontweight="bold", pad=3)
    return im


def figure_3_board_goal(data: dict[str, pd.DataFrame]) -> Path:
    """Principal claim: agent rankings vary across board and stopping rule."""
    summary = data["board_summary"]
    fig, axes = plt.subplots(1, 3, figsize=(7.05, 2.65), sharey=True)
    for idx, board in enumerate(BOARD_ORDER):
        subset = summary[summary.board == board]
        matrix = subset.pivot(index="agent", columns="end_condition", values="win_points_rate")
        matrix = matrix.reindex(index=AGENT_ORDER, columns=END_ORDER) * 100
        im = annotated_heatmap(axes[idx], matrix, board, cmap="RdYlBu", vmin=0, vmax=100)
        axes[idx].set_xticks(range(3), ["Fixed", "Goal 10", "Goal 40"], rotation=28, ha="right")
        axes[idx].set_yticks(range(len(AGENT_ORDER)), [AGENT_LABELS[a] for a in AGENT_ORDER])
        panel_label(axes[idx], chr(ord("A") + idx))
    cax = fig.add_axes([.942, .20, .014, .68])
    cbar = fig.colorbar(im, cax=cax)
    cbar.set_label("Win points (%)")
    cbar.ax.tick_params(labelsize=6.2)
    fig.subplots_adjust(left=.115, right=.915, top=.89, bottom=.20, wspace=.16)
    return export_figure(fig, "03_board_goal_performance")


def figure_4_efficiency_order(data: dict[str, pd.DataFrame]) -> Path:
    """Principal claim: more computation does not guarantee stronger play."""
    overall = data["overall"].set_index("agent").reindex(AGENT_ORDER)
    seat = data["seat"].pivot(index="agent", columns="seat", values="win_points_rate").reindex(AGENT_ORDER)
    fig, axes = plt.subplots(1, 2, figsize=(7.05, 2.55), gridspec_kw={"width_ratios": [1.12, .88]})
    ax = axes[0]
    offsets = {
        "rule": (5, 7), "mcts": (7, -12), "expectimax_d3": (-48, 14),
        "expectimax_d2": (7, -10), "greedy": (7, -9), "random": (5, 5),
    }
    for agent, row in overall.iterrows():
        x = max(row.milliseconds_per_decision, .001)
        y = 100 * row.win_points_rate
        ax.scatter(x, y, s=34, color=COLORS[agent], edgecolor="white", linewidth=.55, zorder=3)
        dx, dy = offsets[agent]
        ax.annotate(AGENT_LABELS[agent], (x, y), xytext=(dx, dy), textcoords="offset points",
                    fontsize=6.1, ha="left", va="center")
    ax.set_xscale("log")
    ax.set_xlabel("Weighted mean decision time (ms; log scale)")
    ax.set_ylabel("Win points (%)")
    ax.set_title("Performance-cost trade-off", loc="left", fontweight="bold")
    ax.axhline(50, color="#626A71", linestyle="--", linewidth=.65)
    clean_axis(ax, "both"); panel_label(ax, "A")

    delta = 100 * (seat["first"] - seat["second"])
    ax = axes[1]
    y = np.arange(len(AGENT_ORDER))
    ax.barh(y, delta, color=[COLORS[a] for a in AGENT_ORDER], height=.65)
    ax.axvline(0, color="#4B5359", linewidth=.7)
    ax.set_yticks(y, [AGENT_LABELS[a] for a in AGENT_ORDER])
    ax.invert_yaxis()
    ax.set_xlabel("First - second seat (percentage points)")
    ax.set_title("Move-order sensitivity", loc="left", fontweight="bold")
    clean_axis(ax, "x"); panel_label(ax, "B")
    fig.subplots_adjust(left=.10, right=.99, top=.88, bottom=.22, wspace=.39)
    return export_figure(fig, "04_efficiency_and_order")


def figure_5_decks(data: dict[str, pd.DataFrame]) -> Path:
    """Principal claim: changing only deck composition shifts relative performance."""
    summary = data["deck_summary"]
    fig, axes = plt.subplots(1, 2, figsize=(7.05, 2.88), gridspec_kw={"width_ratios": [.9, 1.35]})
    ax = axes[0]
    x = np.arange(len(DECK_ORDER)); bottom = np.zeros(len(DECK_ORDER))
    for card_idx, (card, color) in enumerate(zip(CARD_LABELS, CARD_COLORS)):
        values = np.array([DECK_COUNTS[d][card_idx] for d in DECK_ORDER])
        ax.bar(x, values, bottom=bottom, color=color, width=.72, label=card)
        bottom += values
    ax.set_xticks(x, ["Default", "Movement", "Capture", "Swap"], rotation=25, ha="right")
    ax.set_ylabel("Cards in 28-card deck")
    ax.set_title("Controlled deck compositions", loc="left", fontweight="bold")
    legend_handles, legend_labels = ax.get_legend_handles_labels()
    clean_axis(ax); panel_label(ax, "A")

    matrix = summary.pivot(index="agent", columns="deck", values="win_points_rate")
    matrix = matrix.reindex(index=AGENT_ORDER, columns=DECK_ORDER) * 100
    im = annotated_heatmap(axes[1], matrix, "Agent performance", cmap="RdYlBu", vmin=0, vmax=100)
    axes[1].set_xticks(range(4), ["Default", "Movement", "Capture", "Swap"], rotation=25, ha="right")
    axes[1].set_yticks(range(len(AGENT_ORDER)), [AGENT_LABELS[a] for a in AGENT_ORDER])
    panel_label(axes[1], "B")
    cbar = fig.colorbar(im, ax=axes[1], fraction=.045, pad=.025)
    cbar.set_label("Win points (%)")
    fig.legend(legend_handles, legend_labels, ncol=5, frameon=False,
               loc="lower center", bbox_to_anchor=(.5, .005),
               handlelength=1.1, columnspacing=.9)
    fig.subplots_adjust(left=.09, right=.96, top=.88, bottom=.30, wspace=.35)
    return export_figure(fig, "05_deck_composition")


def figure_6_depth(data: dict[str, pd.DataFrame]) -> Path:
    """Principal claim: depth adds steep cost without uniform head-to-head benefit."""
    direct = data["direct_depth"]
    d3 = direct[direct.agent == "expectimax_d3"].pivot(index="board", columns="end_condition", values="win_points_rate")
    d3 = d3.reindex(index=BOARD_ORDER, columns=END_ORDER) * 100
    bounded = data["depth_summary"]
    depth_agents = ["expectimax_d2", "expectimax_d3", "expectimax_d4"]
    fig, axes = plt.subplots(1, 3, figsize=(7.05, 2.75), gridspec_kw={"width_ratios": [1.2, 1, 1]})

    im = annotated_heatmap(axes[0], d3, "Depth 3 vs depth 2", cmap="RdYlBu", vmin=0, vmax=100)
    axes[0].set_xticks(range(3), ["Fixed", "Goal 10", "Goal 40"], rotation=28, ha="right")
    axes[0].set_yticks(range(3), BOARD_ORDER)
    panel_label(axes[0], "A")
    cbar = fig.colorbar(im, ax=axes[0], fraction=.055, pad=.03)
    cbar.ax.set_title("WP (%)", fontsize=6.3, pad=3)

    for panel, metric, title, ylabel, log in [
        (1, "milliseconds_per_decision", "Bounded computation", "Mean ms/decision", True),
        (2, "win_points_rate", "Bounded performance", "Win points (%)", False),
    ]:
        ax = axes[panel]
        x = np.arange(3); width = .23
        for i, agent in enumerate(depth_agents):
            vals = bounded[bounded.agent == agent].set_index("board").reindex(BOARD_ORDER)[metric]
            if metric == "win_points_rate": vals = vals * 100
            ax.bar(x + (i - 1) * width, vals, width, color=COLORS[agent], label=AGENT_LABELS[agent])
        ax.set_xticks(x, ["Default", "Bottleneck", "Inner ring"], rotation=28, ha="right")
        ax.set_ylabel("ms/decision" if log else ylabel, labelpad=1)
        ax.set_title(title, loc="left", fontweight="bold")
        if log: ax.set_yscale("log")
        else: ax.axhline(50, color="#626A71", linestyle="--", linewidth=.65)
        clean_axis(ax); panel_label(ax, chr(ord("A") + panel))
    legend_handles, legend_labels = axes[1].get_legend_handles_labels()
    fig.legend(legend_handles, legend_labels, ncol=3, frameon=False,
               loc="lower center", bbox_to_anchor=(.67, .005), fontsize=6.0)
    fig.subplots_adjust(left=.105, right=.995, top=.88, bottom=.30, wspace=.60)
    return export_figure(fig, "06_expectimax_depth")


def figure_7_net(data: dict[str, pd.DataFrame]) -> Path:
    """Principal claim: net launchers are a recurring but minority capture mode."""
    net = data["net_main_summary"].set_index("agent").reindex(AGENT_ORDER)
    fig, axes = plt.subplots(1, 2, figsize=(7.05, 2.48), gridspec_kw={"width_ratios": [1.2, .8]})
    x = np.arange(len(AGENT_ORDER))
    axes[0].bar(x, net.adjacent, color="#76B7B2", label="Adjacent")
    axes[0].bar(x, net.net, bottom=net.adjacent, color="#F28E2B", label="Net launcher")
    axes[0].set_ylim(0, 1.18 * float(net.total_captures.max()))
    axes[0].set_xticks(x, [AGENT_LABELS[a] for a in AGENT_ORDER], rotation=26, ha="right")
    axes[0].set_ylabel("Recorded capture actions")
    axes[0].set_title("Capture-mode counts", loc="left", fontweight="bold")
    axes[0].legend(frameon=False, ncol=2, loc="upper center", bbox_to_anchor=(.5, 1.02))
    clean_axis(axes[0]); panel_label(axes[0], "A")

    share = 100 * net.net_share
    y = np.arange(len(AGENT_ORDER))
    axes[1].barh(y, share, color=[COLORS[a] for a in AGENT_ORDER], height=.65)
    axes[1].set_yticks(y, [AGENT_LABELS[a] for a in AGENT_ORDER])
    axes[1].invert_yaxis()
    axes[1].set_xlabel("Net launches among captures (%)")
    axes[1].set_title("Within-agent share", loc="left", fontweight="bold")
    for yi, value in zip(y, share):
        axes[1].text(value + .35, yi, f"{value:.1f}", va="center", fontsize=6.1)
    axes[1].set_xlim(0, max(share) + 5)
    clean_axis(axes[1], "x"); panel_label(axes[1], "B")
    fig.subplots_adjust(left=.09, right=.99, top=.88, bottom=.23, wspace=.37)
    return export_figure(fig, "07_net_launcher")


def refresh_data_legends(data: dict[str, pd.DataFrame]) -> None:
    """Insert data-dependent denominators without weakening standalone legends."""
    net = data["net_main_summary"]
    total = int(net.total_captures.sum())
    launches = int(net.net.sum())
    ordered = net.sort_values("net_share")
    low, high = ordered.iloc[0], ordered.iloc[-1]
    LEGENDS["net"] = (
        "<b>Figure 7: Net launches are a recurring but minority capture mode.</b> "
        f"<b>(A)</b> Adjacent and net-launcher capture actions reconstructed from all per-turn logs in the "
        f"1,080-game main and deck suite ({total:,} captures; {launches:,} net launches). Counts are events, "
        "not games, and therefore reflect both opportunity and agent behavior. "
        "<b>(B)</b> Net launches as a percentage of each agent's captures, with exact percentages printed beside "
        "the bars. Expectimax depth 4 is excluded because it appears only in the smaller bounded feasibility "
        f"study. Across the displayed agents, the net share ranges from {100*low.net_share:.1f}% "
        f"({AGENT_LABELS[low.agent]}) to {100*high.net_share:.1f}% ({AGENT_LABELS[high.agent]})."
    )


def make_figures(data: dict[str, pd.DataFrame]) -> dict[str, Path]:
    configure_plotting()
    refresh_data_legends(data)
    return {
        "mechanics": figure_1_mechanics(),
        "boards": figure_2_boards(),
        "board_goal": figure_3_board_goal(data),
        "efficiency": figure_4_efficiency_order(data),
        "decks": figure_5_decks(data),
        "depth": figure_6_depth(data),
        "net": figure_7_net(data),
    }


PAGE_W, PAGE_H = letter
MARGIN = .67 * inch
GUTTER = .24 * inch
CONTENT_W = PAGE_W - 2 * MARGIN
COL_W = (CONTENT_W - GUTTER) / 2


def styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("title", parent=base["Title"], fontName="Times-Bold",
                                fontSize=16, leading=18, alignment=TA_CENTER, spaceAfter=5),
        "author": ParagraphStyle("author", parent=base["Normal"], fontName="Times-Roman",
                                 fontSize=10, leading=12, alignment=TA_CENTER, spaceAfter=5),
        "abstract": ParagraphStyle("abstract", parent=base["Normal"], fontName="Times-Roman",
                                   fontSize=8.7, leading=10.2, alignment=TA_JUSTIFY),
        "h1": ParagraphStyle("h1", parent=base["Heading1"], fontName="Times-Bold",
                              fontSize=11.5, leading=13, spaceBefore=8, spaceAfter=3, keepWithNext=True),
        "h2": ParagraphStyle("h2", parent=base["Heading2"], fontName="Times-Bold",
                              fontSize=10, leading=11.5, spaceBefore=6, spaceAfter=2, keepWithNext=True),
        "body": ParagraphStyle("body", parent=base["BodyText"], fontName="Times-Roman",
                                fontSize=8.8, leading=10.55, alignment=TA_JUSTIFY, spaceAfter=4),
        "caption": ParagraphStyle("caption", parent=base["BodyText"], fontName="Times-Roman",
                                   fontSize=7.55, leading=8.8, alignment=TA_LEFT, spaceBefore=2, spaceAfter=3),
        "small": ParagraphStyle("small", parent=base["BodyText"], fontName="Times-Roman",
                                 fontSize=7.5, leading=8.7, alignment=TA_LEFT, spaceAfter=2),
        "ref": ParagraphStyle("ref", parent=base["BodyText"], fontName="Times-Roman",
                               fontSize=7.6, leading=8.8, leftIndent=9, firstLineIndent=-9, spaceAfter=2),
    }


def para(text: str, st: dict[str, ParagraphStyle], kind: str = "body") -> Paragraph:
    return Paragraph(text, st[kind])


def image_at_width(path: Path, width: float) -> Image:
    """Scale a figure without changing its data geometry or aspect ratio."""
    img = Image(str(path))
    img.drawHeight = width * img.imageHeight / img.imageWidth
    img.drawWidth = width
    img.hAlign = "CENTER"
    return img


class CoursePaperDoc(BaseDocTemplate):
    def __init__(self, path: Path):
        super().__init__(str(path), pagesize=letter, leftMargin=MARGIN, rightMargin=MARGIN,
                         topMargin=.55 * inch, bottomMargin=.55 * inch,
                         title="Graph Card Control",
                         author="Omri Avital and Itai Reder")
        col_h = PAGE_H - 1.10 * inch
        left = Frame(MARGIN, .55 * inch, COL_W, col_h, leftPadding=0, rightPadding=4,
                     topPadding=0, bottomPadding=0, id="left")
        right = Frame(MARGIN + COL_W + GUTTER, .55 * inch, COL_W, col_h,
                      leftPadding=4, rightPadding=0, topPadding=0, bottomPadding=0, id="right")

        title_h = 2.35 * inch
        first_top = Frame(MARGIN, PAGE_H - .55 * inch - title_h, CONTENT_W, title_h,
                          leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=4, id="title")
        first_col_h = PAGE_H - 1.10 * inch - title_h
        first_body = Frame(MARGIN, .55 * inch, CONTENT_W, first_col_h, leftPadding=0,
                           rightPadding=0, topPadding=3, bottomPadding=0, id="first_body")

        wide_h = 3.18 * inch
        wide = Frame(MARGIN, PAGE_H - .55 * inch - wide_h, CONTENT_W, wide_h,
                     leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=2, id="wide")
        lower_h = PAGE_H - 1.10 * inch - wide_h
        lower_left = Frame(MARGIN, .55 * inch, COL_W, lower_h, leftPadding=0,
                           rightPadding=4, topPadding=4, bottomPadding=0, id="wide_left")
        lower_right = Frame(MARGIN + COL_W + GUTTER, .55 * inch, COL_W, lower_h,
                            leftPadding=4, rightPadding=0, topPadding=4, bottomPadding=0, id="wide_right")
        balanced_wide = Frame(MARGIN, PAGE_H - .55 * inch - wide_h, CONTENT_W, wide_h,
                              leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=2,
                              id="balanced_wide")
        balanced_lower = Frame(MARGIN, .55 * inch, CONTENT_W, lower_h, leftPadding=0,
                               rightPadding=0, topPadding=4, bottomPadding=0,
                               id="balanced_lower")
        full = Frame(MARGIN, .55 * inch, CONTENT_W, col_h, leftPadding=0,
                     rightPadding=0, topPadding=0, bottomPadding=0, id="full")

        self.addPageTemplates([
            PageTemplate("First", [first_top, first_body], onPage=self.footer),
            PageTemplate("TwoCol", [left, right], onPage=self.footer),
            PageTemplate("WideTop", [wide, lower_left, lower_right], onPage=self.footer),
            PageTemplate("WideTopBalanced", [balanced_wide, balanced_lower], onPage=self.footer),
            PageTemplate("FullWide", [full], onPage=self.footer),
        ])

    @staticmethod
    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("Times-Roman", 7)
        canvas.setFillColor(colors.HexColor("#555555"))
        canvas.drawCentredString(PAGE_W / 2, .30 * inch, str(doc.page))
        canvas.restoreState()


def compact_table(rows: list[list[str]], widths: list[float]) -> Table:
    cell = ParagraphStyle("table_cell", fontName="Times-Roman", fontSize=7.0, leading=8.1)
    head = ParagraphStyle("table_head", fontName="Times-Bold", fontSize=7.0, leading=8.1,
                          textColor=colors.white)
    wrapped = [[Paragraph(str(v), head if r == 0 else cell) for v in row] for r, row in enumerate(rows)]
    table = Table(wrapped, colWidths=widths, repeatRows=1, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#315E7D")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F1F4F6")]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 2.5), ("RIGHTPADDING", (0, 0), (-1, -1), 2.5),
        ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LINEBELOW", (0, 0), (-1, -1), .35, colors.HexColor("#8B969E")),
    ]))
    return table


def fixed_columns(left: list, right: list) -> Table:
    """Place known short article sections in stable, non-splitting columns."""
    table = Table([[left, right]], colWidths=[COL_W, COL_W], hAlign="LEFT", vAlign="TOP")
    table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (0, 0), 0),
        ("RIGHTPADDING", (0, 0), (0, 0), GUTTER / 2),
        ("LEFTPADDING", (1, 0), (1, 0), GUTTER / 2),
        ("RIGHTPADDING", (1, 0), (1, 0), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    return table


LEGENDS = {
    "mechanics": "<b>Figure 1: Turn structure and capture modes.</b> "
        "<b>(A)</b> The player selects a public card, acts, scores, refills the market randomly, and tests the stopping rule. With no legal card the player passes; two passes refresh the market. "
        "<b>(B)</b> The five card types and their ranges. Mobilize moves two pieces when possible and otherwise one. "
        "<b>(C)</b> A regular (melee) capture targets an orthogonally adjacent enemy. A net launcher uses an adjacent friendly pair and the first occupied cell on an outward range-3 ray. Both score three points and respawn the target; objective cells score at turn end. Blue is the acting side and red the target; diagrams are schematic.",
    "boards": "<b>Figure 2: Three board geometries define the spatial experimental factor.</b> "
        "<b>(A)</b> Default open 5x5 board. <b>(B)</b> Bottleneck 7x7 board with blocked central lanes. <b>(C)</b> Inner-ring 7x7 board with more widely separated spawns and a four-point center. Blue and red circles mark the initial cells of players A and B; yellow cells are end-of-turn objectives labeled by points; dark cells are blocked. Coordinates and piece identities are omitted because the JSON board definitions are the authoritative executable specification.",
    "board_goal": "<b>Figure 3: Agent rankings vary across board geometry and stopping rule.</b> "
        "<b>(A-C)</b> Win points for the six agents on the default, bottleneck, and inner-ring boards, respectively. Columns are a fixed 25-turn-per-player horizon and point goals of 10 or 40; the turn cap remains a safety bound in goal games. Each cell contains 30 agent-game observations: five opponents, both player orders, and three matched seeds. A win contributes 1, a draw 0.5, and a loss 0. Color and printed values both encode win points (%); 50% denotes parity across opponents. Conditions are separate tests, not pooled replicates.",
    "efficiency": "<b>Figure 4: Additional computation does not yield a monotonic performance gain.</b> "
        "<b>(A)</b> Aggregate win points versus weighted mean decision time across the 12 main and independent-deck conditions. Each agent has 360 agent-game observations; time is total recorded decision time divided by non-pass decisions and is shown on a logarithmic axis. The dashed line marks 50% win points. "
        "<b>(B)</b> First-seat minus second-seat win-points rate for the same conditions (180 agent-game observations per seat and agent). Positive values favor moving first. Colors identify agents in both panels; labels provide a redundant non-color encoding.",
    "decks": "<b>Figure 5: Independently changing deck composition shifts relative agent performance.</b> "
        "<b>(A)</b> Counts of the five action cards in each 28-card deck; stacked segments sum to 28. "
        "<b>(B)</b> Win points on the default board under the fixed 25-turn-per-player horizon. Each cell contains 30 agent-game observations across five opponents, both player orders, and three matched seeds. Color and printed values encode win points (%). The default condition is the shared control; the three alternatives change only card counts while retaining the two-pass market refresh.",
    "depth": "<b>Figure 6: Deeper expectimax is substantially slower and is not uniformly stronger.</b> "
        "<b>(A)</b> Depth-3 win points in direct depth-3 versus depth-2 matches for all nine board/stopping-rule combinations. Each cell summarizes six games (three matched seeds in both player orders); 50% denotes parity. "
        "<b>(B-C)</b> Weighted mean decision time and win points, respectively, in the bounded goal-20 feasibility study. Bars summarize six agent-game observations per board and depth; all variants use a top-2 action cap. Runtime uses a logarithmic axis and the dashed performance line marks 50%. Depth 4 used one seed and is interpreted as a feasibility measurement; depth 5 exceeded 120 s for one benchmark decision and depth 6 was not run.",
    "net": "<b>Figure 7: Net launches are a recurring but minority capture mode.</b> "
        "<b>(A)</b> Adjacent and net-launcher capture actions reconstructed from all per-turn logs in the 1,080-game main and deck suite. Counts are events, not games, and therefore reflect both opportunity and agent behavior. "
        "<b>(B)</b> Net launches as a percentage of each agent's captures, with exact percentages printed beside the bars. Expectimax depth 4 is excluded because it appears only in the smaller bounded feasibility study. Across the displayed agents, the net share ranges from 9.5% to 23.5%.",
}


def wide_figure(story: list, st: dict[str, ParagraphStyle], path: Path, key: str,
                height: float, after: list, next_template: str | None = "TwoCol",
                balance_after: bool = True) -> None:
    story.extend([NextPageTemplate("WideTopBalanced"), PageBreak()])
    img = image_at_width(path, CONTENT_W)
    story.extend([img, para(LEGENDS[key], st, "caption"), FrameBreak()])
    if balance_after:
        story.append(BalancedColumns(after, nCols=2, innerPadding=GUTTER,
                                     leftPadding=0, rightPadding=0,
                                     topPadding=0, bottomPadding=0))
    else:
        story.extend(after)
    if next_template:
        story.append(NextPageTemplate(next_template))


def build_paper(data: dict[str, pd.DataFrame], figs: dict[str, Path]) -> Path:
    st = styles(); PDF_DIR.mkdir(parents=True, exist_ok=True)
    pdf = PDF_DIR / "graph_card_control_course_paper.pdf"
    story: list = []
    overall = data["overall"].set_index("agent").reindex(AGENT_ORDER)
    seat = data["seat"].pivot(index="agent", columns="seat", values="win_points_rate").reindex(AGENT_ORDER)
    ranked = data["overall"].sort_values("win_points_rate", ascending=False)
    rank_text = ", ".join(
        f"{AGENT_LABELS[row.agent]} ({100*row.win_points_rate:.1f}%)"
        for row in ranked.itertuples(index=False)
    )
    search_ranked = ranked[ranked.agent.isin(["mcts", "expectimax_d2", "expectimax_d3"])]
    best = ranked.iloc[0]
    best_search = search_ranked.iloc[0]
    d3_rows = data["direct_depth"].query("agent == 'expectimax_d3'")
    d3_direct_n = int(d3_rows.games.sum())
    d3_direct_wp = float(np.average(d3_rows.win_points_rate, weights=d3_rows.games))
    d2_ms = float(overall.loc["expectimax_d2", "milliseconds_per_decision"])
    d3_ms = float(overall.loc["expectimax_d3", "milliseconds_per_decision"])
    seat_delta = 100 * (seat["first"] - seat["second"])
    largest_seat_agent = seat_delta.abs().idxmax()
    game_duration = data["game_summary"].set_index(["board", "end_condition"])
    goal10_duration = [float(game_duration.loc[(board, "Goal 10"), "mean_total_turns"]) for board in BOARD_ORDER]
    goal40_duration = [float(game_duration.loc[(board, "Goal 40"), "mean_total_turns"]) for board in BOARD_ORDER]
    deck_table = data["deck_summary"].pivot(index="agent", columns="deck", values="win_points_rate")
    deck_leader = deck_table.idxmax().iloc[0]
    deck_leader_low = float(deck_table.loc[deck_leader].min())
    deck_leader_high = float(deck_table.loc[deck_leader].max())
    d2_decks = deck_table.loc["expectimax_d2"]
    main_net = data["net_main_summary"]
    all_net = data["net_summary"]
    main_net_count, main_capture_count = int(main_net.net.sum()), int(main_net.total_captures.sum())
    all_net_count, all_capture_count = int(all_net.net.sum()), int(all_net.total_captures.sum())
    action_summary = data["action_summary"].set_index("agent").reindex(AGENT_ORDER)

    story.extend([
        para("Graph Card Control: Evaluating Search Agents in a Stochastic Abstract Strategy Game", st, "title"),
        para("Omri Avital (208693341) &nbsp;&nbsp; Itai Reder (318850781)<br/>237-2-5513 Search Methods in Artificial Intelligence", st, "author"),
        para(f"<b>Abstract.</b> We introduce Graph Card Control, a configurable two-player, stochastic, perfect-information game for controlled comparison of bounded search implementations and transparent baselines. The only random event is replacement of a selected card in a three-card public market. We evaluate random, greedy, rule-based, Monte Carlo tree search (MCTS), and depth-2/depth-3 expectimax agents across three board geometries, three stopping rules, player order, and independently varied deck composition. The corrected suite contains 1,116 replay-validated games and prevents agents from conditioning on hidden deck order. {AGENT_LABELS[best.agent]} achieved the highest aggregate win-points rate ({100*best.win_points_rate:.1f}%) at {best.milliseconds_per_decision:.1f} ms per decision. Among search agents, {AGENT_LABELS[best_search.agent]} reached {100*best_search.win_points_rate:.1f}% at {best_search.milliseconds_per_decision:.1f} ms. Depth-3 expectimax cost {d3_ms/d2_ms:.1f} times depth 2 and obtained {100*d3_direct_wp:.1f}% in their direct matches. Board geometry, stopping rule, deck composition, and player order all changed outcomes. The results characterize these fixed-budget implementations; they are not universal algorithm rankings.", st, "abstract"),
        FrameBreak(),
        BalancedColumns([
        para("Introduction and Literature Review", st, "h1"),
        para("Game playing provides a controlled setting in which states, actions, stochastic transitions, and utility can be specified exactly. This project asks a narrower empirical question: when an unfamiliar game combines adversarial choice with a public stochastic card refill, how do bounded search agents compare with transparent baselines under changes to geometry, stopping rule, deck composition, and move order? The course explicitly identifies a custom strategy game with search-based and threshold agents as a suitable research direction.", st),
        para("Graph Card Control is a stochastic, perfect-information game. Exact lookahead therefore requires decision nodes for both players and expectation over replacement-card outcomes. Ballard's *-minimax analysis showed how bounds can prune trees containing chance nodes (Ballard 1983), while Monte Carlo *-minimax later combined sparse sampling with stochastic adversarial search (Lanctot et al. 2013). These works motivate expectimax as the structurally appropriate exact model and also predict its computational difficulty when both action and chance branching are present.", st),
        para("MCTS offers an alternative allocation of computation. Coulom (2006) integrated Monte Carlo evaluation with selective tree growth, and Kocsis and Szepesvari (2006) introduced UCT, establishing consistency and finite-sample error bounds for Monte Carlo planning. Sparse sampling can avoid enumerating every stochastic successor (Kearns, Mansour, and Ng 1999). Our corrected MCTS samples replacement cards from the public composition on every traversal, aggregates outcomes on stochastic action edges, and treats the opponent as a minimizing player. Expectimax instead enumerates the complete known refill distribution after selecting its bounded action beam.", st),
        para("The broader MCTS literature separates selection, expansion, simulation, and backup, with playing strength depending on choices in every phase (Browne et al. 2012). This matters for interpretation: our comparison tests one explicit budget and rollout design, while expectimax spends computation on exhaustive chance backup inside a depth limit. A result for either implementation is therefore evidence about a cost-allocation choice, not about all members of the algorithm family.", st),
        para("Deeper search is not automatically better when leaf evaluation is approximate. Pearl (1983) demonstrated that repeated minimax backup can amplify evaluation noise and, in pathological cases, degrade decisions with depth. The choice-function framework likewise formalizes when pruning the considered action set can preserve policy improvement (Issakkimuthu, Fern, and Tadepalli 2020). These results are directly relevant to our top-2 expectimax cap and to interpreting the observed depth/runtime trade-off rather than treating depth as an unconditional quality scale.", st),
        para("We organize the evaluation around five questions. Which agent is strongest across the chosen boards and stopping rules? How much decision time does that performance require? Does moving first change the comparison? Does independently changing the deck alter the ranking? Finally, do deeper expectimax and the net-launcher mechanic produce evidence of qualitatively different play? These are descriptive questions about the implemented system; they are not claims of universal algorithm superiority.", st),
        para("General game playing emphasizes evaluating agents on games not engineered around a single solver (Genesereth, Love, and Pell 2005). Our contribution is accordingly methodological rather than algorithmic: (i) an executable stochastic game with configurable geometry, objectives, decks, and stopping rules; (ii) a reproducible matched-order experiment system; and (iii) an empirical comparison that includes computational cost and behavior, not only win rate.", st),
        ], nCols=2, innerPadding=GUTTER, leftPadding=0, rightPadding=0,
           topPadding=0, bottomPadding=0),
    ])

    wide_figure(story, st, figs["mechanics"], "mechanics", 2.10 * inch, [
        para("Methodology", st, "h1"),
        para("Game model", st, "h2"),
        para("Players alternate turns on an orthogonal grid and control three pieces each. The current player selects one legal action from a public three-card market. Movement cards reposition pieces; Capture scores three points through an adjacent attack or net launcher; Swap exchanges a friendly and enemy piece within Manhattan distance three. Captured pieces respawn, preventing elimination. Objective cells score at the end of every occupying turn. After a played card is discarded, its market slot is refilled by a draw from the known remaining composition. Thus the state is fully observable while the next refill is stochastic (Figure 1).", st),
        KeepTogether([para("A pass occurs only when all visible cards are unusable. Preliminary experiments identified repeated passes as an absorbing market failure, so every final condition refreshes all three market cards after two consecutive passes. Any legal move resets the counter. This rule change is fixed across the final suite and is not itself an experimental factor.", st)]),
        para("Implementation", st, "h2"),
        para("The Python 3.10+ rules engine represents a state as an immutable record and applies actions through a shared transition function. Random-number-generator state is carried inside the game state, making a game deterministic once its seed is fixed. Legal-action generation and state transitions are shared by human, baseline, and search agents, preventing agent-specific rule implementations. Runtime dependencies and analysis libraries are declared in the repository requirements file.", st),
        para("Replacement draws can be forced during search and replay. Agents receive the executable state, which retains a shuffled deck for deterministic match execution, but corrected successor evaluation never consults that hidden ordering. Greedy and rule-based evaluation use a deterministic most-probable public refill solely for action ordering. Expectimax backs up the exact probability-weighted value of every remaining card type; its top-2 beam is ordered in the appropriate maximizing or minimizing direction. MCTS resamples the public draw distribution with an agent-local random generator on every action-edge traversal and alternates root-player maximization with opponent minimization (100 simulations, rollout depth 10, exploration constant 1.4). Reversing the hidden deck while holding all public fields fixed changed zero tested choices for greedy, rule, expectimax depth 2, and MCTS.", st),
    ])

    board_methods_left = [
        para("Boards, decks, and stopping rules", st, "h2"),
        para("The main factorial varies three symmetric boards (Figure 2) and three stopping rules: a fixed 25 turns per player, first to 10 points, and first to 40 points. Goal games retain a 50-turn-per-player safety cap. Goal 10 emphasizes openings, whereas goal 40 permits sustained positional control. The inner-ring center awards four points, deliberately making center occupation more valuable than a three-point capture.", st),
        para("Deck composition is tested independently on the default board at the fixed horizon. The 28-card control deck contains 8 Move 1, 6 Move 2, 5 Mobilize, 5 Capture, and 4 Swap cards. Movement-, capture-, and swap-heavy variants alter these counts without changing card behavior. This reduced design avoids an uninterpretable full cross-product while preserving a common control.", st),
        para("Agents", st, "h2"),
        para("Random samples uniformly from legal actions. Greedy selects the immediate public-information successor with the highest shared heuristic. Rule prioritizes captures and objectives, then uses that heuristic for tie-breaking. Expectimax alternates maximizing and minimizing decision nodes and expands exact replacement-card probabilities at depth 2 or 3; its top-2 beam keeps the best root-player actions at maximizing nodes and the strongest replies at minimizing nodes. MCTS uses 100 simulations, rollout depth 10, sampled public chance outcomes, and adversarial selection. Deterministic minimax is excluded because it neither models chance nodes nor answers the stochastic-search question.", st),
        para("The shared evaluation is a weighted difference between the players: score (100), objective-cell control (10), distance to the nearest objective (2), capture threats (15), net-launcher potential (20), swap potential (8), piece safety (10), and legal-action mobility (1). The dominant score weight encodes the game objective; all weights are fixed across final conditions and stored in every mode configuration.", st),
    ]
    board_methods_right = [
        para("Experimental design and metrics", st, "h2"),
        para("Each board/stopping-rule condition contains every ordered non-self pair among six agents and three matched game seeds (90 games). Mirrored orders reuse the seed, allowing direct first-versus-second comparison. Four independent deck conditions contribute 360 games, but the default fixed-horizon control is shared with the board study; the 12 unique main/deck modes therefore contain 1,080 games. A bounded goal-20 depth study adds 36 games across the three boards, for 1,116 total.", st),
        para("A win contributes one win point, a draw one half, and a loss zero. The engine measures each action-selection call with a monotonic high-resolution clock; runtime is total logged decision time divided by non-pass decisions. The corrected suite ran sequentially on an Intel Core i5-9600K under 64-bit Python 3.12.13 and Windows 10 (build 19045), so timing supports within-machine comparisons rather than portable benchmarks. Behavioral analysis reconstructs adjacent and net-launcher captures from per-turn logs. Percentages are descriptive: a direct main matchup has six games, and the same seeds recur across conditions. Each mode stores its complete configuration. All 1,116 logs replayed from forced draws matched the recorded final outcomes.", st),
        para("Analysis plan", st, "h2"),
        para("The primary comparison asks which agents perform well across boards and stopping rules. Secondary analyses examine first-versus-second order, performance per unit decision time, isolated deck composition, direct expectimax-depth matchups, and adjacent versus net-launcher captures. The deck study is analyzed separately because it was deliberately not crossed with board geometry.", st),
        para("No null-hypothesis significance tests or confidence intervals are reported. Games within a matched seed and repeated conditions are not independent, while direct matchups contain only six games. The analysis therefore reports denominators, matched contrasts, and calibrated descriptive conclusions; confirmatory inference is left to a larger independent-seed experiment.", st),
    ]
    wide_figure(story, st, figs["boards"], "boards", 1.98 * inch,
                [fixed_columns(board_methods_left, board_methods_right)],
                balance_after=False)

    table_rows = [["Agent", "N", "Win points", "Margin", "ms/decision"]]
    for agent, row in overall.sort_values("win_points_rate", ascending=False).iterrows():
        ms = row.milliseconds_per_decision
        table_rows.append([AGENT_LABELS[agent], str(int(row.games)), f"{100*row.win_points_rate:.1f}%",
                           f"{row.mean_margin:+.2f}", f"{ms:.2f}" if ms >= 0.005 else "<0.01"])
    net_by_agent = main_net.set_index("agent")
    move1_low, move1_high = 100*action_summary.move1_share.min(), 100*action_summary.move1_share.max()
    capture_low, capture_high = 100*action_summary.capture_share.min(), 100*action_summary.capture_share.max()
    capture_rates = pd.Series({
        agent: net_by_agent.loc[agent, "total_captures"] / overall.loc[agent, "games"]
        for agent in AGENT_ORDER
    })
    capture_second = 100 * action_summary.capture_share.nsmallest(2).iloc[-1]
    net_share_min_agent = net_by_agent.net_share.idxmin()
    net_share_min = float(net_by_agent.net_share.min())
    non_rule_shares = net_by_agent.net_share.loc[["mcts", "greedy", "expectimax_d2", "expectimax_d3"]]
    net_share_others_low = float(non_rule_shares.min())
    net_share_others_high = float(non_rule_shares.max())

    wide_figure(story, st, figs["board_goal"], "board_goal", 2.20 * inch, [
        para("Experimental Results", st, "h1"),
        para("Overall performance", st, "h2"),
        para(f"Across the 12 unique main and deck conditions, the aggregate order was {rank_text}. {AGENT_LABELS[best.agent]} therefore provided the strongest observed performance-cost trade-off at its measured budget. This pooled ranking is descriptive rather than universal: board geometry and stopping rule changed the relative ordering (Figure 3).", st),
        para("Table 1: Aggregate results across the 12 unique main/deck conditions.", st, "small"),
        compact_table(table_rows, [.78*inch, .28*inch, .52*inch, .43*inch, .58*inch]),
        para("Board geometry and stopping rule", st, "h2"),
        para(f"The heatmaps show that no pooled percentage captures every condition. Goal-10 games were especially short on the four-point inner-ring board, where one or two successful center occupations can determine the result. Mean combined duration was {goal10_duration[0]:.1f}, {goal10_duration[1]:.1f}, and {goal10_duration[2]:.1f} turns for goal 10 on the default, bottleneck, and inner-ring boards, respectively, compared with {goal40_duration[0]:.1f}, {goal40_duration[1]:.1f}, and {goal40_duration[2]:.1f} turns for goal 40. Goal 10 is therefore an opening-focused stress test rather than a substitute for longer evaluation.", st),
        para("Runtime and move order", st, "h2"),
        para(f"Performance did not increase monotonically with decision time (Figure 4A). Measured costs were {overall.loc['rule','milliseconds_per_decision']:.1f} ms for rule, {overall.loc['greedy','milliseconds_per_decision']:.1f} ms for greedy, {d2_ms:.1f} ms for expectimax depth 2, {overall.loc['mcts','milliseconds_per_decision']:.1f} ms for MCTS, and {d3_ms:.1f} ms for expectimax depth 3. Depth 3 was {d3_ms/d2_ms:.1f} times slower than depth 2, while their aggregate win-points difference was {100*(overall.loc['expectimax_d3','win_points_rate']-overall.loc['expectimax_d2','win_points_rate']):+.1f} percentage points. Additional lookahead changed decisions, but its cost was not matched by a uniform direct advantage.", st),
        para(f"Move-order effects were smaller than the full spread between agents but remained visible (Figure 4B). The largest absolute first-minus-second contrast was {seat_delta[largest_seat_agent]:+.1f} percentage points for {AGENT_LABELS[largest_seat_agent]}; MCTS was {seat_delta['mcts']:+.1f}, depth-3 expectimax {seat_delta['expectimax_d3']:+.1f}, and rule {seat_delta['rule']:+.1f}. Because every pair is mirrored with the same seed, these contrasts control opponent identity and the seeded refill process more closely than an unmatched tournament.", st),
        para("Independent deck-composition test", st, "h2"),
        para(f"Changing card frequencies shifted relative performance even though board, stopping rule, market refresh, and seed design were fixed (Figure 5). {AGENT_LABELS[deck_leader]} led every deck ({100*deck_leader_low:.1f}-{100*deck_leader_high:.1f}%), but the mid-ranking reordered: depth-2 expectimax ranged from {100*d2_decks.min():.1f}% under the {d2_decks.idxmin().lower()} deck to {100*d2_decks.max():.1f}% under the {d2_decks.idxmax().lower()} deck and fell behind greedy when movement cards dominated. Thus a ranking from one action distribution should not be generalized to the game family. Because deck and board were not crossed, this experiment estimates deck effects on the default board, not deck-by-geometry interactions.", st),
        para("Expectimax depth", st, "h2"),
        para(f"Across nine direct board/stopping-rule cells, depth 3 obtained {100*d3_direct_wp:.1f}% of win points against depth 2 over {d3_direct_n} agent-game observations (Figure 6A). The bounded study shows the computational reason for stopping at depth 4: runtime rises steeply on all boards (Figure 6B), while the corresponding performance estimates use only one seed and are unstable (Figure 6C). Depth 5 exceeded 120 seconds for one benchmark decision; depth 6 was therefore not run. The branching structure and approximate top-2 beam make this result plausible, but the experiment does not isolate a causal mechanism and does not establish search pathology.", st),
        para("Dominant strategies and net-launcher use", st, "h2"),
        para(f"Rule is explicitly capture-first and objective-first, whereas greedy and expectimax optimize a broader multi-term heuristic that can trade immediate score for mobility, safety, or formation potential. In the main suite, Move 1 was every agent's most-used card ({move1_low:.1f}-{move1_high:.1f}% of played actions), consistent with its 8/28 deck prevalence. Capture-card shares, by contrast, separated the agents: {AGENT_LABELS[action_summary.capture_share.idxmin()]} played captures in only {capture_low:.1f}% of its actions against {capture_second:.1f}-{capture_high:.1f}% for the other agents, and capture rates ranged from {capture_rates.min():.2f} ({AGENT_LABELS[capture_rates.idxmin()]}) to {capture_rates.max():.2f} ({AGENT_LABELS[capture_rates.idxmax()]}) per agent-game. Deliberate capture seeking therefore distinguishes every non-random agent from the random baseline, but these summaries still do not isolate a winning mechanism; that requires policy and heuristic-weight ablation. Complete action counts are available in the accompanying results archive (<font name='Courier'>tables/16_action_usage_summary.csv</font>).", st),
        para(f"The net launcher accounted for {all_net_count:,} of {all_capture_count:,} captures ({100*all_net_count/all_capture_count:.1f}%) across the complete suite. In the comparable 1,080-game main/deck suite, {main_net_count:,} of {main_capture_count:,} captures were net launches ({100*main_net_count/main_capture_count:.1f}%; Figure 7). Net use also varied by agent: {AGENT_LABELS[net_share_min_agent]} fired nets in {100*net_share_min:.1f}% of its captures, against {100*net_share_others_low:.1f}-{100*net_share_others_high:.1f}% for MCTS, greedy, and the expectimax variants. This frequency establishes that the mechanic affects play, but event counts alone do not establish that using it causes wins.", st),
    ], next_template=None)

    # Pair related wide figures on full-width pages. This retains final-size
    # readability while avoiding half-empty pages in the two-column article.
    story.extend([NextPageTemplate("FullWide"), PageBreak()])
    for key in ("efficiency", "decks"):
        img = image_at_width(figs[key], CONTENT_W)
        story.extend([img, para(LEGENDS[key], st, "caption"), Spacer(1, .05 * inch)])

    story.extend([NextPageTemplate("FullWide"), PageBreak()])
    for key in ("depth", "net"):
        img = image_at_width(figs[key], CONTENT_W)
        story.extend([img, para(LEGENDS[key], st, "caption"), Spacer(1, .05 * inch)])

    code_availability = para("<b><font size='10'>Code and data availability</font></b><br/>"
        "Source code, board and deck definitions, experiment configurations, per-game results, move logs, analysis scripts, and figure-generation code are available at <link href='https://github.com/Naharda/Grid_Control_Game.git'>github.com/Naharda/Grid_Control_Game</link>. The report figures are generated by <font name='Courier'>analysis/build_course_paper.py</font>; complete final-suite tables are indexed under <font name='Courier'>final_results/</font>.", st)
    final_left = [
        para("Experimental Conclusions<br/>and Summary", st, "h1"),
        para(f"The project achieved its objective of constructing a reproducible stochastic game domain and comparing bounded search implementations with meaningful baselines. Under the tested settings, {AGENT_LABELS[best.agent]} produced the highest aggregate win-points rate, {AGENT_LABELS[best_search.agent]} led the evaluated search agents, and depth-3 expectimax was substantially more expensive than depth 2 without a uniform direct advantage. Board geometry, score goal, deck composition, and player order all changed outcomes, so one pooled tournament ranking would obscure important structure.", st),
        para("The main limitations are statistical and budgetary. Direct depth matchups contain six games per condition, only three seeds support the main cells, seeds recur across conditions, and no confidence intervals are claimed. Decks were varied independently rather than factorially with boards. Expectimax retains a heuristic top-2 beam, depth 4 uses one seed, and MCTS samples rather than exhaustively expands chance outcomes. MCTS and expectimax were not matched by wall-clock budget, and the shared heuristic was not tuned on a separate training set. The corrected agents pass hidden-deck-order invariance tests, but the API still carries the execution deck, so architectural separation would be safer than relying on tested discipline. Future work should increase independent paired seeds, compare equal-time performance curves, ablate heuristic terms, and test *-minimax or progressive-widening variants where chance branching grows.", st),
    ]
    final_right = [
        code_availability,
        para("References", st, "h1"),
        para("Ballard, B. W. 1983. The *-minimax search procedure for trees containing chance nodes. <i>Artificial Intelligence</i> 21(3): 327-350.", st, "ref"),
        para("Browne, C. B.; Powley, E.; Whitehouse, D.; Lucas, S. M.; Cowling, P. I.; Rohlfshagen, P.; Tavener, S.; Perez, D.; Samothrakis, S.; and Colton, S. 2012. A survey of Monte Carlo tree search methods. <i>IEEE Transactions on Computational Intelligence and AI in Games</i> 4(1): 1-43.", st, "ref"),
        para("Coulom, R. 2006. Efficient selectivity and backup operators in Monte-Carlo tree search. In <i>Computers and Games</i>, 72-83.", st, "ref"),
        para("Genesereth, M.; Love, N.; and Pell, B. 2005. General game playing: Overview of the AAAI competition. <i>AI Magazine</i> 26(2): 62-72.", st, "ref"),
        para("Issakkimuthu, M.; Fern, A.; and Tadepalli, P. 2020. The choice function framework for online policy improvement. In <i>Proceedings of AAAI</i>, 10178-10185.", st, "ref"),
        para("Kearns, M.; Mansour, Y.; and Ng, A. Y. 1999. A sparse sampling algorithm for near-optimal planning in large Markov decision processes. In <i>Proceedings of IJCAI</i>, 1324-1331.", st, "ref"),
        para("Kocsis, L.; and Szepesvari, C. 2006. Bandit based Monte-Carlo planning. In <i>ECML</i>, 282-293.", st, "ref"),
        para("Lanctot, M.; Saffidine, A.; Veness, J.; Archibald, C.; and Winands, M. H. M. 2013. Monte Carlo *-minimax search. In <i>Proceedings of IJCAI</i>, 580-586.", st, "ref"),
        para("Pearl, J. 1983. On the nature of pathology in game searching. <i>Artificial Intelligence</i> 20(4): 427-453.", st, "ref"),
    ]
    final_columns = Table([[final_left, final_right]], colWidths=[COL_W, COL_W],
                          hAlign="LEFT", vAlign="TOP")
    final_columns.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (0, 0), 0),
        ("RIGHTPADDING", (0, 0), (0, 0), GUTTER / 2),
        ("LEFTPADDING", (1, 0), (1, 0), GUTTER / 2),
        ("RIGHTPADDING", (1, 0), (1, 0), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.extend([NextPageTemplate("FullWide"), PageBreak(), final_columns])

    CoursePaperDoc(pdf).build(story)
    # Keep the historical "final_report" filename as a compatibility alias so
    # there is only one submission manuscript and no stale Figure 1 to open.
    shutil.copyfile(pdf, PDF_DIR / "graph_card_control_final_report.pdf")
    return pdf


def write_supporting_files(data: dict[str, pd.DataFrame]) -> None:
    OUT.mkdir(parents=True, exist_ok=True); TABLE_DIR.mkdir(parents=True, exist_ok=True)
    data["overall"].to_csv(TABLE_DIR / "01_overall_agent_performance.csv", index=False)
    data["board_summary"].to_csv(TABLE_DIR / "02_board_goal_performance.csv", index=False)
    data["deck_summary"].to_csv(TABLE_DIR / "03_deck_performance.csv", index=False)
    data["direct_depth"].to_csv(TABLE_DIR / "04_direct_expectimax_depth.csv", index=False)
    data["depth_summary"].to_csv(TABLE_DIR / "05_bounded_expectimax_depth.csv", index=False)
    data["net_main_summary"].to_csv(TABLE_DIR / "06_net_launcher.csv", index=False)
    data["coverage"].to_csv(TABLE_DIR / "07_coverage_manifest.csv", index=False)
    data["game_summary"].to_csv(TABLE_DIR / "08_condition_game_summary.csv", index=False)
    data["seat"].to_csv(TABLE_DIR / "09_move_order_summary.csv", index=False)
    data["main_results"].to_csv(TABLE_DIR / "10_all_main_and_deck_games.csv", index=False)
    data["main_long"].to_csv(TABLE_DIR / "11_all_main_agent_games.csv", index=False)
    data["depth_results"].to_csv(TABLE_DIR / "12_all_depth_games.csv", index=False)
    data["depth_long"].to_csv(TABLE_DIR / "13_all_depth_agent_games.csv", index=False)
    data["net_events"].to_csv(TABLE_DIR / "14_all_capture_events.csv", index=False)
    all_games = pd.concat([
        data["main_results"].assign(study="main_and_deck"),
        data["depth_results"].assign(study="bounded_depth"),
    ], ignore_index=True).sort_values(["study", "mode", "pair", "game"])
    all_games.to_csv(TABLE_DIR / "15_all_1116_game_results.csv", index=False)
    data["action_summary"].to_csv(TABLE_DIR / "16_action_usage_summary.csv", index=False)
    data["action_events"].to_csv(TABLE_DIR / "17_all_played_card_events.csv", index=False)

    legends = ["# Figure legends", ""]
    for i, key in enumerate(["mechanics", "boards", "board_goal", "efficiency", "decks", "depth", "net"], 1):
        plain = LEGENDS[key].replace("<b>", "**").replace("</b>", "**")
        legends.extend([f"## Figure {i}", "", plain, ""])
    (OUT / "FIGURE_LEGENDS.md").write_text("\n".join(legends), encoding="utf-8")

    decision_rows = [
        ["figure", "principal_claim", "chosen_layout", "why", "verification"],
        ["1", "A visible public market isolates one stochastic refill event", "three equal panels: turn, cards, two framed capture modes/scoring", "contrasts regular and net captures without crowding the narrow panel", "render at final 7.05-inch width; inspect all labels and arrows"],
        ["2", "Geometry and objective value are controlled factors", "three symmetric board panels", "preserves spatial comparison and equal scale", "compare cells against boards/*.json"],
        ["3", "Rankings vary by board and stopping rule", "three matched annotated heatmaps", "compact 54-cell comparison with exact values", "cross-check against board_summary"],
        ["4", "Computation is not monotonically related to performance", "log scatter plus horizontal order bars", "pairs cost and strength while separating seat effect", "cross-check overall and seat tables"],
        ["5", "Deck composition shifts performance", "stacked composition bars plus heatmap", "shows manipulation and outcome in one reading path", "counts sum to 28; cross-check deck_summary"],
        ["6", "Depth has steep cost without uniform benefit", "direct heatmap plus two grouped bar panels", "separates matched comparison, runtime, and bounded strength", "cross-check direct_depth/depth_summary"],
        ["7", "Net launchers are recurrent but a minority", "stacked counts plus normalized horizontal bars", "shows denominators and within-agent shares", "cross-check net_main_summary; exclude incomparable d4"],
    ]
    with (OUT / "FIGURE_DECISION_LOG.csv").open("w", newline="", encoding="utf-8") as handle:
        csv.writer(handle).writerows(decision_rows)

    overall = data["overall"].set_index("agent")
    d3 = data["direct_depth"].query("agent == 'expectimax_d3'")
    d3_wp = float(np.average(d3.win_points_rate, weights=d3.games))
    main_net = data["net_main_summary"]
    all_net = data["net_summary"]
    ledger_rows = [
        ["claim_or_decision", "status", "evidence_locator", "confidence_or_check"],
        ["Required course chapter sequence", "requirement", "project_instructions_en.md", "implemented with the required named sections"],
        ["AAAI-style format is recommended", "requirement", "project_instructions_en.md", "US-Letter two-column approximation; exact AAAI style-file compliance is not claimed"],
        ["Corrected suite contains 1,116 games", "observed", "tables/07_coverage_manifest.csv", "15 modes; all expected result rows and logs present"],
        ["All 1,116 logs replay to recorded outcomes", "observed", "analysis/validate_reduced_factorial.py", "1,116/1,116 passed"],
        [f"Rule aggregate win points: {100*overall.loc['rule','win_points_rate']:.1f}%", "derived", "tables/01_overall_agent_performance.csv", "360 agent-game observations"],
        [f"MCTS aggregate win points: {100*overall.loc['mcts','win_points_rate']:.1f}%", "derived", "tables/01_overall_agent_performance.csv", "fixed 100-simulation implementation"],
        [f"Expectimax d3 direct win points vs d2: {100*d3_wp:.1f}%", "derived", "tables/04_direct_expectimax_depth.csv", f"{int(d3.games.sum())} agent-game observations across nine conditions"],
        [f"Main-suite net launches: {int(main_net.net.sum()):,}/{int(main_net.total_captures.sum()):,}", "derived", "tables/06_net_launcher.csv", "events from the comparable 1,080-game main/deck cohort"],
        [f"Full-suite net launches: {int(all_net.net.sum()):,}/{int(all_net.total_captures.sum()):,}", "derived", "tables/14_all_capture_events.csv", "all 1,116 games; event count is not a causal win analysis"],
        ["Dominant action profiles are availability-conditioned", "derived", "tables/16_action_usage_summary.csv", "most-used played card and shares; no causal claim"],
        ["Expectimax expands refill chance outcomes exactly", "observed", "src/search/expectimax.py", "possible_draws with forced draw_card successors"],
        ["MCTS samples public chance and minimizes opponent choices", "observed", "src/search/mcts.py", "stochastic action edges; adversarial UCB selection"],
        ["Agent choices are invariant to hidden-deck reversal in tested states", "observed", "HIDDEN_DECK_AUDIT.md", "0 sensitive checkpoints for all four audited agents"],
        ["Decision times are within-machine comparisons", "limitation", "RUNTIME_ENVIRONMENT.md", "sequential i5-9600K / CPython 3.12.13 run"],
        ["Authors", "metadata", "user-provided", "Omri Avital 208693341; Itai Reder 318850781"],
    ]
    with (OUT / "EVIDENCE_LEDGER.csv").open("w", newline="", encoding="utf-8") as handle:
        csv.writer(handle).writerows(ledger_rows)

    index = """# Course-format final paper

- Final PDF: `../../output/pdf/graph_card_control_course_paper.pdf`
- [Figure legends](FIGURE_LEGENDS.md)
- [Figure decision log](FIGURE_DECISION_LOG.csv)
- [Figure layout audit](FIGURE_LAYOUT_AUDIT.md)
- [Evidence ledger](EVIDENCE_LEDGER.csv)
- [Assaf-style content audit](ASSAF_STYLE_AUDIT.md)
- [Hidden-deck sensitivity audit](HIDDEN_DECK_AUDIT.md)
- [Corrected-agent rerun record](CORRECTED_RERUN_PLAN.md)
- [Literature-review search plan](LITERATURE_REVIEW_SEARCH_PLAN.md)
- [Runtime environment](RUNTIME_ENVIRONMENT.md)
- `figures/` contains seven 300-dpi previews and editable vector PDF exports.
- `tables/` contains 19 sorted source, event-level, audit, and complete-results exports.
- Reproduction script: `../../analysis/build_course_paper.py`
- Final artifact validator: `../../analysis/validate_course_paper.py`

The paper follows the course-required chapter sequence and an AAAI-like US-Letter two-column layout. The corrected public-information rerun is the sole source for the final quantitative claims.
"""
    (OUT / "00_INDEX.md").write_text(index, encoding="utf-8")


def main() -> None:
    data = prepare_data()
    figs = make_figures(data)
    write_supporting_files(data)
    pdf = build_paper(data, figs)
    print(pdf)


if __name__ == "__main__":
    main()
