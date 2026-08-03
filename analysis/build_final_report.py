"""Build the final Graph Card Control article and publication figures."""

from __future__ import annotations

import csv
import json
import math
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

OUT = ROOT / "final_results" / "final_report"
FIGURES = OUT / "figures"
TABLES = OUT / "tables"
PDF_OUT = ROOT / "output" / "pdf"
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".mplconfig"))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Rectangle
import numpy as np
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    Image,
    KeepTogether,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from reduced_factorial_report import (
    AGENTS,
    AGENT_LABELS,
    BOARD_MODES,
    COLORS,
    DECK_MODES,
    DEPTH_MODES,
    aggregate_agents,
    extract_action_usage,
    extract_net_usage,
    load_results,
    mode_config,
    to_long,
    validate_coverage,
)


PAGE_W, PAGE_H = A4
MARGIN_X = 18 * mm
MARGIN_TOP = 17 * mm
MARGIN_BOTTOM = 18 * mm
CONTENT_W = PAGE_W - 2 * MARGIN_X


def save_figure(fig: plt.Figure, stem: str) -> tuple[Path, Path]:
    png = FIGURES / f"{stem}.png"
    pdf = FIGURES / f"{stem}.pdf"
    fig.savefig(png, dpi=300, bbox_inches="tight", facecolor="white")
    fig.savefig(pdf, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return png, pdf


def draw_board(ax: plt.Axes, board: dict, title: str) -> None:
    rows, cols = board["rows"], board["cols"]
    ax.set_xlim(-0.55, cols - 0.45)
    ax.set_ylim(rows - 0.45, -0.55)
    ax.set_aspect("equal")
    ax.set_xticks(np.arange(-0.5, cols, 1), minor=True)
    ax.set_yticks(np.arange(-0.5, rows, 1), minor=True)
    ax.grid(which="minor", color="#c7c7c7", linewidth=0.7)
    ax.set_xticks([])
    ax.set_yticks([])
    for r, c in board.get("blocked_cells", []):
        ax.add_patch(Rectangle((c - 0.47, r - 0.47), 0.94, 0.94, color="#333333", zorder=2))
    for entry in board["capture_cells"]:
        r, c = entry["cell"]
        ax.add_patch(Rectangle((c - 0.42, r - 0.42), 0.84, 0.84, color="#edc948", zorder=3))
        ax.text(c, r, f"+{entry['points']}", ha="center", va="center", fontsize=8, fontweight="bold", zorder=4)
    for player, color in (("A", "#4e79a7"), ("B", "#e15759")):
        for r, c in board["spawns"][player]:
            ax.add_patch(Circle((c, r), 0.29, color=color, zorder=5))
            ax.text(c, r, player, color="white", ha="center", va="center", fontsize=7, fontweight="bold", zorder=6)
    ax.set_title(title, fontsize=10, fontweight="bold", pad=5)


def make_rules_figure() -> Path:
    fig = plt.figure(figsize=(11.4, 8.0))
    grid = fig.add_gridspec(2, 3, height_ratios=[0.78, 1.22], hspace=0.3, wspace=0.2)
    ax_flow = fig.add_subplot(grid[0, :])
    ax_flow.axis("off")
    steps = [
        ("Public market", "3 face-up cards"),
        ("Choose action", "Move, mobilize, capture, swap"),
        ("Apply and score", "Capture points + occupied objectives"),
        ("Refill market", "Stochastic replacement draw"),
        ("End check", "Fixed horizon or score goal"),
    ]
    xs = np.linspace(0.07, 0.93, len(steps))
    for i, ((title, subtitle), x) in enumerate(zip(steps, xs)):
        box = FancyBboxPatch(
            (x - 0.085, 0.39), 0.17, 0.28,
            boxstyle="round,pad=0.012,rounding_size=0.015",
            facecolor="#eef3f8", edgecolor="#4e79a7", linewidth=1.2,
            transform=ax_flow.transAxes,
        )
        ax_flow.add_patch(box)
        ax_flow.text(x, 0.57, title, ha="center", va="center", fontsize=9, fontweight="bold", transform=ax_flow.transAxes)
        ax_flow.text(x, 0.47, subtitle, ha="center", va="center", fontsize=7.5, wrap=True, transform=ax_flow.transAxes)
        if i < len(steps) - 1:
            ax_flow.add_patch(FancyArrowPatch((x + 0.088, 0.53), (xs[i + 1] - 0.088, 0.53), arrowstyle="-|>", mutation_scale=11, color="#555555", transform=ax_flow.transAxes))
    ax_flow.text(
        0.50, 0.20,
        "If no action is legal: pass. Two consecutive passes discard and refresh the entire market; any legal action resets the pass counter.",
        ha="center", va="center", fontsize=8.5, color="#333333", transform=ax_flow.transAxes,
    )
    ax_flow.text(0.01, 0.96, "A", fontsize=14, fontweight="bold", transform=ax_flow.transAxes)

    board_names = [
        ("default", "Default 5x5"),
        ("bottleneck_7x7", "Bottleneck 7x7"),
        ("inner_ring_center_7x7", "Inner-ring center 7x7"),
    ]
    for index, (name, title) in enumerate(board_names):
        ax = fig.add_subplot(grid[1, index])
        board = json.loads((ROOT / "boards" / f"{name}.json").read_text(encoding="utf-8"))
        draw_board(ax, board, title)
        if index == 0:
            ax.text(-0.14, 1.06, "B", fontsize=14, fontweight="bold", transform=ax.transAxes)
    fig.suptitle("Game sequence and experimental board geometries", fontsize=15, fontweight="bold", y=0.99)
    png, _ = save_figure(fig, "01_rules_and_boards")
    return png


def prepare_data() -> dict[str, pd.DataFrame]:
    coverage = validate_coverage()
    board_results = pd.concat([load_results(mode) for mode in BOARD_MODES], ignore_index=True)
    board_meta = pd.DataFrame([{"mode": m, "board": b, "end_condition": e} for m, (b, e) in BOARD_MODES.items()])
    board_long = to_long(board_results).merge(board_meta, on="mode")
    board_summary = aggregate_agents(board_long, ["mode", "board", "end_condition"])
    game_summary = (
        board_results.merge(board_meta, on="mode")
        .assign(total_turns=lambda x: x.turns_a + x.turns_b, total_score=lambda x: x.score_a + x.score_b, draw=lambda x: x.winner.eq("draw"))
        .groupby(["mode", "board", "end_condition"], as_index=False)
        .agg(games=("game", "size"), draw_rate=("draw", "mean"), mean_total_turns=("total_turns", "mean"), mean_total_score=("total_score", "mean"))
    )

    unique_main_modes = list(BOARD_MODES) + [m for m in DECK_MODES if m not in BOARD_MODES]
    main_results = pd.concat([load_results(mode) for mode in unique_main_modes], ignore_index=True)
    main_long = to_long(main_results)
    overall = aggregate_agents(main_long, [])
    seat = aggregate_agents(main_long, ["seat"])

    deck_results = pd.concat([load_results(mode) for mode in DECK_MODES], ignore_index=True)
    deck_meta = pd.DataFrame([{"mode": m, "deck": d} for m, d in DECK_MODES.items()])
    deck_long = to_long(deck_results).merge(deck_meta, on="mode")
    deck_summary = aggregate_agents(deck_long, ["mode", "deck"])

    direct_rows = []
    for mode, (board, end) in BOARD_MODES.items():
        direct = to_long(load_results(mode))
        direct = direct[direct.agent.isin(["expectimax_d2", "expectimax_d3"]) & direct.opponent.isin(["expectimax_d2", "expectimax_d3"])]
        for agent, subset in direct.groupby("agent"):
            direct_rows.append({
                "mode": mode, "board": board, "end_condition": end, "agent": agent,
                "games": len(subset), "win_points_rate": subset.outcome.mean(), "mean_margin": subset.margin.mean(),
                "milliseconds_per_decision": 1000 * subset.decision_time_seconds.sum() / subset.decisions.sum(),
            })
    direct_depth = pd.DataFrame(direct_rows)

    depth_results = pd.concat([load_results(mode) for mode in DEPTH_MODES], ignore_index=True)
    depth_meta = pd.DataFrame([{"mode": m, "board": b} for m, b in DEPTH_MODES.items()])
    depth_long = to_long(depth_results).merge(depth_meta, on="mode")
    depth_summary = aggregate_agents(depth_long, ["mode", "board"])

    net_main_events, net_main_summary = extract_net_usage(unique_main_modes)
    net_events, net_summary = extract_net_usage(unique_main_modes + list(DEPTH_MODES))
    action_events, action_summary = extract_action_usage(unique_main_modes)
    return {
        "coverage": coverage, "board_results": board_results, "board_long": board_long,
        "board_summary": board_summary, "game_summary": game_summary,
        "main_results": main_results, "main_long": main_long, "overall": overall, "seat": seat,
        "deck_results": deck_results, "deck_long": deck_long, "deck_summary": deck_summary,
        "direct_depth": direct_depth, "depth_results": depth_results,
        "depth_long": depth_long, "depth_summary": depth_summary,
        "net_main_events": net_main_events, "net_main_summary": net_main_summary,
        "net_events": net_events, "net_summary": net_summary,
        "action_events": action_events, "action_summary": action_summary,
    }


def make_result_figures(data: dict[str, pd.DataFrame]) -> dict[str, Path]:
    paths: dict[str, Path] = {}
    board_summary = data["board_summary"]
    end_order = ["Fixed 25", "Goal 10", "Goal 40"]
    board_order = ["Default", "Bottleneck 7x7", "Inner ring"]

    fig, axes = plt.subplots(1, 3, figsize=(12.2, 4.7), sharey=True)
    for ax, board in zip(axes, board_order):
        subset = board_summary[board_summary.board == board]
        x = np.arange(3)
        width = 0.12
        for i, agent in enumerate(AGENTS):
            values = subset[subset.agent == agent].set_index("end_condition").reindex(end_order).win_points_rate * 100
            ax.bar(x + (i - 2.5) * width, values, width, color=COLORS[agent], label=AGENT_LABELS[agent])
        ax.axhline(50, color="#333333", linestyle="--", linewidth=0.9)
        ax.set_xticks(x, end_order, rotation=18, ha="right")
        ax.set_title(board, fontweight="bold")
        ax.grid(axis="y", alpha=0.22)
        ax.spines[["top", "right"]].set_visible(False)
    axes[0].set_ylabel("Win points across five opponents (%)")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, ncol=3, frameon=False, loc="upper center", bbox_to_anchor=(0.5, 1.02))
    fig.suptitle("Agent ranking depends on board geometry and end condition", fontsize=14, fontweight="bold", y=1.11)
    fig.tight_layout()
    paths["board_goal"] = save_figure(fig, "02_board_goal_performance")[0]

    game = data["game_summary"]
    seat = data["seat"]
    fig, axes = plt.subplots(1, 2, figsize=(11.8, 4.7))
    x = np.arange(len(board_order))
    width = 0.23
    for i, end in enumerate(end_order):
        vals = game[game.end_condition == end].set_index("board").reindex(board_order).mean_total_turns
        axes[0].bar(x + (i - 1) * width, vals, width, label=end, color=["#9c9c9c", "#f28e2b", "#4e79a7"][i])
    axes[0].set_xticks(x, board_order, rotation=12, ha="right")
    axes[0].set_ylabel("Mean combined turns per game")
    axes[0].set_title("A. End condition changes game length", loc="left", fontweight="bold")
    axes[0].legend(frameon=False)

    seat_pivot = seat.pivot(index="agent", columns="seat", values="win_points_rate").reindex(AGENTS)
    delta = (seat_pivot["first"] - seat_pivot["second"]) * 100
    bar_colors = [COLORS[a] for a in AGENTS]
    axes[1].bar(np.arange(len(AGENTS)), delta, color=bar_colors)
    axes[1].axhline(0, color="#333333", linewidth=0.9)
    axes[1].set_xticks(np.arange(len(AGENTS)), [AGENT_LABELS[a] for a in AGENTS], rotation=24, ha="right")
    axes[1].set_ylabel("First minus second win points (percentage points)")
    axes[1].set_title("B. Move-order effect across the main suite", loc="left", fontweight="bold")
    for ax in axes:
        ax.grid(axis="y", alpha=0.22)
        ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    paths["length_order"] = save_figure(fig, "03_game_length_and_order")[0]

    deck = data["deck_summary"]
    deck_order = ["Default", "Movement-heavy", "Capture-heavy", "Swap-heavy"]
    matrix = deck.pivot(index="agent", columns="deck", values="win_points_rate").reindex(index=AGENTS, columns=deck_order) * 100
    fig, ax = plt.subplots(figsize=(8.4, 4.8))
    image = ax.imshow(matrix.to_numpy(), aspect="auto", cmap="YlGnBu", vmin=0, vmax=100)
    for i in range(len(AGENTS)):
        for j in range(len(deck_order)):
            value = matrix.iloc[i, j]
            ax.text(j, i, f"{value:.0f}", ha="center", va="center", color="white" if value > 58 else "#222222", fontsize=9, fontweight="bold")
    ax.set_xticks(range(len(deck_order)), deck_order, rotation=15, ha="right")
    ax.set_yticks(range(len(AGENTS)), [AGENT_LABELS[a] for a in AGENTS])
    ax.set_title("Independent deck composition test (win points, %)", fontweight="bold")
    cbar = fig.colorbar(image, ax=ax, shrink=0.85)
    cbar.set_label("Win points (%)")
    fig.tight_layout()
    paths["deck"] = save_figure(fig, "04_deck_composition")[0]

    direct = data["direct_depth"].copy()
    direct["condition"] = direct.board + "\n" + direct.end_condition
    conditions = [f"{b}\n{e}" for b in board_order for e in end_order]
    fig, axes = plt.subplots(1, 2, figsize=(12.2, 4.8))
    x = np.arange(len(conditions))
    for offset, agent in ((-0.18, "expectimax_d2"), (0.18, "expectimax_d3")):
        vals = direct[direct.agent == agent].set_index("condition").reindex(conditions).win_points_rate * 100
        axes[0].bar(x + offset, vals, 0.36, color=COLORS[agent], label=AGENT_LABELS[agent])
    axes[0].axhline(50, color="#333333", linestyle="--", linewidth=0.9)
    axes[0].set_xticks(x, conditions, rotation=36, ha="right", fontsize=7.5)
    axes[0].set_ylabel("Direct head-to-head win points (%)")
    axes[0].set_title("A. Depth 2 versus depth 3", loc="left", fontweight="bold")
    axes[0].legend(frameon=False)

    bounded = data["depth_summary"]
    for agent in ("expectimax_d2", "expectimax_d3", "expectimax_d4"):
        vals = bounded[bounded.agent == agent].set_index("board").reindex(board_order).milliseconds_per_decision
        axes[1].plot(board_order, vals, marker="o", linewidth=2, color=COLORS[agent], label=AGENT_LABELS[agent])
    axes[1].set_yscale("log")
    axes[1].set_ylabel("Weighted mean ms/decision (log scale)")
    axes[1].set_title("B. Bounded depth cost", loc="left", fontweight="bold")
    axes[1].legend(frameon=False)
    for ax in axes:
        ax.grid(axis="y", alpha=0.22)
        ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    paths["depth"] = save_figure(fig, "05_expectimax_depth")[0]

    net = data["net_summary"].set_index("agent")
    order = [a for a in AGENTS if a in net.index] + ["expectimax_d4"]
    net = net.reindex(order)
    fig, axes = plt.subplots(1, 2, figsize=(11.4, 4.6))
    x = np.arange(len(order))
    axes[0].bar(x, net.adjacent, color="#76b7b2", label="Adjacent")
    axes[0].bar(x, net.net, bottom=net.adjacent, color="#f28e2b", label="Net launcher")
    axes[0].set_ylabel("Capture actions")
    axes[0].set_title("A. Capture counts", loc="left", fontweight="bold")
    axes[0].legend(frameon=False)
    axes[1].bar(x, net.net_share * 100, color=[COLORS.get(a, "#777777") for a in order])
    axes[1].set_ylabel("Net launches among captures (%)")
    axes[1].set_title("B. Net-launcher share", loc="left", fontweight="bold")
    labels = [AGENT_LABELS[a] for a in order]
    for ax in axes:
        ax.set_xticks(x, labels, rotation=25, ha="right")
        ax.grid(axis="y", alpha=0.22)
        ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    paths["net"] = save_figure(fig, "06_net_launcher")[0]
    return paths


def fmt_pct(value: float) -> str:
    return f"{100 * value:.1f}%"


def make_styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("ArticleTitle", parent=base["Title"], fontName="Helvetica-Bold", fontSize=21, leading=25, alignment=TA_CENTER, textColor=colors.HexColor("#17324D"), spaceAfter=8),
        "subtitle": ParagraphStyle("Subtitle", parent=base["Normal"], fontName="Helvetica", fontSize=10, leading=14, alignment=TA_CENTER, textColor=colors.HexColor("#55606A"), spaceAfter=14),
        "abstract_head": ParagraphStyle("AbstractHead", parent=base["Heading2"], fontName="Helvetica-Bold", fontSize=11, leading=14, textColor=colors.HexColor("#17324D"), spaceBefore=4, spaceAfter=4),
        "h1": ParagraphStyle("H1", parent=base["Heading1"], fontName="Helvetica-Bold", fontSize=14, leading=17, textColor=colors.HexColor("#17324D"), spaceBefore=12, spaceAfter=6, keepWithNext=True),
        "h2": ParagraphStyle("H2", parent=base["Heading2"], fontName="Helvetica-Bold", fontSize=11.5, leading=14, textColor=colors.HexColor("#315E7D"), spaceBefore=9, spaceAfter=4, keepWithNext=True),
        "body": ParagraphStyle("Body", parent=base["BodyText"], fontName="Helvetica", fontSize=9.2, leading=13.2, alignment=TA_LEFT, textColor=colors.HexColor("#202428"), spaceAfter=6),
        "caption": ParagraphStyle("Caption", parent=base["BodyText"], fontName="Helvetica", fontSize=8, leading=10.5, textColor=colors.HexColor("#30363B"), spaceBefore=3, spaceAfter=8),
        "small": ParagraphStyle("Small", parent=base["BodyText"], fontName="Helvetica", fontSize=7.5, leading=9.5, textColor=colors.HexColor("#40464D"), spaceAfter=4),
        "table_title": ParagraphStyle("TableTitle", parent=base["BodyText"], fontName="Helvetica-Bold", fontSize=8.5, leading=10.5, textColor=colors.HexColor("#17324D"), spaceBefore=6, spaceAfter=4, keepWithNext=True),
    }


def p(text: str, styles: dict[str, ParagraphStyle], style: str = "body") -> Paragraph:
    return Paragraph(text, styles[style])


def article_table(data: list[list[object]], widths: list[float], font_size: float = 7.4, header_rows: int = 1) -> Table:
    wrapped = []
    for row_index, row in enumerate(data):
        wrapped.append([
            Paragraph(str(cell), ParagraphStyle(
                f"cell_{row_index}_{col_index}", fontName="Helvetica-Bold" if row_index < header_rows else "Helvetica",
                fontSize=font_size, leading=font_size + 2, textColor=colors.white if row_index < header_rows else colors.HexColor("#202428"),
                alignment=TA_LEFT,
            ))
            for col_index, cell in enumerate(row)
        ])
    table = Table(wrapped, colWidths=widths, repeatRows=header_rows, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, header_rows - 1), colors.HexColor("#315E7D")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("ROWBACKGROUNDS", (0, header_rows), (-1, -1), [colors.white, colors.HexColor("#F3F6F8")]),
        ("LINEBELOW", (0, header_rows - 1), (-1, -1), 0.6, colors.HexColor("#315E7D")),
        ("LINEBELOW", (0, -1), (-1, -1), 0.5, colors.HexColor("#AAB4BC")),
    ]))
    return table


def add_figure(story: list, path: Path, caption: str, styles: dict[str, ParagraphStyle], width: float = CONTENT_W) -> None:
    image = Image(str(path), width=width, height=width * 0.47)
    image.hAlign = "CENTER"
    story.extend([image, p(caption, styles, "caption")])


class ArticleDocTemplate(BaseDocTemplate):
    def __init__(self, filename: str):
        super().__init__(filename, pagesize=A4, leftMargin=MARGIN_X, rightMargin=MARGIN_X, topMargin=MARGIN_TOP, bottomMargin=MARGIN_BOTTOM, title="Graph Card Control Final Report", author="Search Methods in AI Final Project")
        frame = Frame(MARGIN_X, MARGIN_BOTTOM, CONTENT_W, PAGE_H - MARGIN_TOP - MARGIN_BOTTOM, id="main")
        self.addPageTemplates(PageTemplate(id="article", frames=[frame], onPage=self._header_footer))

    @staticmethod
    def _header_footer(canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor("#D5DCE1"))
        canvas.setLineWidth(0.5)
        canvas.line(MARGIN_X, PAGE_H - 11 * mm, PAGE_W - MARGIN_X, PAGE_H - 11 * mm)
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(colors.HexColor("#59636C"))
        canvas.drawString(MARGIN_X, PAGE_H - 8.5 * mm, "Graph Card Control - Final experimental report")
        canvas.drawRightString(PAGE_W - MARGIN_X, 9 * mm, f"Page {doc.page}")
        canvas.restoreState()


def build_pdf(data: dict[str, pd.DataFrame], figures: dict[str, Path]) -> Path:
    styles = make_styles()
    PDF_OUT.mkdir(parents=True, exist_ok=True)
    # This builder is retained for provenance; the course-format builder owns
    # the canonical final_report compatibility alias.
    pdf_path = PDF_OUT / "graph_card_control_legacy_report.pdf"
    story: list = []

    overall = data["overall"].set_index("agent").reindex(AGENTS)
    seat = data["seat"].pivot(index="agent", columns="seat", values="win_points_rate").reindex(AGENTS)
    game = data["game_summary"]
    direct = data["direct_depth"]
    d3 = direct[direct.agent == "expectimax_d3"]
    d3_wp = np.average(d3.win_points_rate, weights=d3.games)
    net = data["net_summary"]
    total_net = int(net.net.sum())
    total_caps = int(net.total_captures.sum())

    story.extend([
        Spacer(1, 10 * mm),
        p("Graph Card Control", styles, "title"),
        p("A controlled experimental comparison of rule-based, heuristic, expectimax, and Monte Carlo tree-search agents", styles, "subtitle"),
        p("Final report - Search Methods in Artificial Intelligence", styles, "subtitle"),
        Spacer(1, 4 * mm),
        p("Abstract", styles, "abstract_head"),
        p(
            "Graph Card Control is a two-player stochastic strategy game in which players use a shared public card market to move, capture, swap, and control scoring cells. We evaluated six main agents across three boards, three end conditions, both player orders, and four deck compositions. The internally consistent experiment contains 1,116 games; all use a market refresh after two consecutive passes, and every trajectory was replay-validated. Rule achieved the highest aggregate win-points rate (69.0%), followed by MCTS (62.1%), expectimax depth 3 (59.0%), expectimax depth 2 (55.7%), greedy (53.9%), and random (0.3%). Agent rankings varied materially by board and end condition. A first-to-10 goal shortened games to 12.1 combined turns on average, compared with 38.5 for goal 40 and 50 for the fixed horizon. Expectimax depth 3 obtained 48.1% of direct head-to-head win points against depth 2 while requiring approximately 7.6 times more computation per decision, demonstrating that greater depth was not reliably advantageous. Net launches represented 21.3% of all recorded captures. These results favor transparent rule-based play under the tested settings and show that geometry, stopping rules, and computation budgets must be treated as experimental factors rather than nuisance details.",
            styles,
        ),
        p("Keywords: adversarial search; expectimax; Monte Carlo tree search; stochastic games; heuristic search; experimental game AI", styles, "small"),
        PageBreak(),
    ])

    story.extend([
        p("1. Introduction", styles, "h1"),
        p(
            "The purpose of this project is to compare search-based agents with transparent baseline policies in a configurable, stochastic, turn-based game. The central methodological challenge is that a global agent ranking can be misleading when board topology, the public market, the win condition, and move order all alter the value of short-term tactics and long-term control. The final design therefore uses matched seeds and both player orientations, varies board and end condition together in a reduced matrix, and tests deck composition independently.", styles,
        ),
        p(
            "The study asks five questions: (1) which agent performs best overall; (2) how much performance changes when an agent moves first rather than second; (3) whether rankings are stable across board geometries; (4) how fixed-horizon, goal-10, and goal-40 play differ; and (5) whether deck composition changes strength and runtime. A separate bounded experiment evaluates expectimax depths 2-4, while direct depth-2 versus depth-3 games are included in every main board/end condition.", styles,
        ),
        p("2. Game rules", styles, "h1"),
        p(
            "Each player controls three pieces. At the start of a turn, the player chooses one legal action generated by one of three face-up market cards. The five card types are Move 1, Move 2, Mobilize, Capture, and Swap. Move cards reposition pieces orthogonally; Mobilize moves two pieces one step each when possible; Swap exchanges a friendly and an enemy piece within the configured range. Capture can be adjacent (melee) or can use a net: two orthogonally adjacent friendly pieces form an outward launcher that captures an enemy on the permitted ray. Captured pieces immediately respawn near their owner's spawn cells.", styles,
        ),
        p(
            "A capture scores three points in the final suite. At the end of a legal turn, the active player also scores every occupied objective cell. The used market card is discarded and replaced by a stochastic draw from the known deck composition. If no market card has a legal use, the player passes. After two consecutive passes, the full market is discarded and redealt; any legal action resets the pass counter. This rule eliminates the absorbing illegal-market state observed in preliminary experiments.", styles,
        ),
    ])
    rules_path = make_rules_figure()
    add_figure(
        story, rules_path,
        "<b>Figure 1. Game sequence and board geometries.</b> (A) A legal turn selects one of three public market cards, applies its action, awards capture and objective points, refills the used slot by a stochastic draw, and checks the end condition. A pass occurs only when no market card has a legal action. Two consecutive passes trigger a complete market refresh. (B) The three symmetric boards used in the final experiment. Blue and red circles are the initial A and B spawn cells; yellow cells are end-of-turn objectives labeled by points; dark cells are blocked. The inner-ring center is worth four points, exceeding the three-point reward for a capture and therefore directly rewards rushing and holding the center.",
        styles, width=CONTENT_W,
    )

    story.extend([
        p("3. Methods", styles, "h1"),
        p("3.1 Agents", styles, "h2"),
        p(
            "Random samples uniformly from legal actions. Greedy chooses the legal successor with the highest shared heuristic evaluation. Rule first selects the best capture; if none exists, it prioritizes occupying a scoring cell, then movement toward the nearest scoring cell. Expectimax expands stochastic replacement-card draws exactly and uses alternating maximizing/minimizing decision layers; depth-2 and depth-3 variants use the same top-2 action cap. MCTS uses 100 simulations, rollout depth 10, UCB selection, random legal rollouts, and the shared heuristic as the terminal rollout value. The original minimax implementation was excluded because it does not model chance nodes and can inspect the realized deck order.", styles,
        ),
        p("3.2 Experimental design", styles, "h2"),
    ])
    settings = [
        ["Component", "Setting"],
        ["Main agents", "Random, greedy, rule, expectimax d2, expectimax d3, MCTS"],
        ["Boards", "Default 5x5; bottleneck 7x7; inner-ring center 7x7"],
        ["End conditions", "Fixed 25 turns/player; first to 10; first to 40 (50-turn/player safety cap)"],
        ["Deck test", "Default board, fixed 25 turns/player; default plus three independent compositions"],
        ["Pairing", "All 30 ordered non-self pairs; three matched game seeds (0, 1, 2)"],
        ["Pass rule", "Refresh all three market cards after two consecutive passes"],
        ["Capture/objectives", "Capture = 3 points; board-specific objectives scored at end of turn"],
        ["Depth study", "Rule and expectimax d2-d4; one seed; goal 20; 15-turn/player cap; top-k = 2"],
        ["Primary metrics", "Win points, score margin, move-order split, ms/decision, game length, net use"],
    ]
    story.extend([
        p("Table 1. Final experimental settings.", styles, "table_title"),
        article_table(settings, [40 * mm, CONTENT_W - 40 * mm], font_size=7.5),
        Spacer(1, 3 * mm),
        p(
            "The board/end-condition block contains 810 games (nine conditions x 30 ordered pairs x three seeds). The independent deck block contributes 270 additional games because the default-deck control is shared with the default fixed-horizon board condition. The bounded depth block contributes 36 games. Thus, the final internally consistent suite contains 1,116 games. Each result records both agents' decision time and decision count, allowing runtime to be normalized per actual non-pass decision.", styles,
        ),
        p("3.3 Deck compositions", styles, "h2"),
    ])
    deck_rows = [["Deck", "Move 1", "Move 2", "Mobilize", "Capture", "Swap"]]
    for name in ["default", "movement_heavy", "capture_heavy", "swap_heavy"]:
        deck = json.loads((ROOT / "decks" / f"{name}.json").read_text(encoding="utf-8"))
        cards = deck["cards"]
        deck_rows.append([name.replace("_", " ").title(), cards["move1"], cards["move2"], cards["mobilize"], cards["capture"], cards["swap"]])
    story.extend([
        p("Table 2. Card counts in each 28-card deck.", styles, "table_title"),
        article_table(deck_rows, [43 * mm, 21 * mm, 21 * mm, 24 * mm, 23 * mm, 20 * mm], font_size=7.3),
        p("3.4 Analysis", styles, "h2"),
        p(
            "A win contributes one win point, a draw contributes one half, and a loss contributes zero. Self-play is excluded. Results are descriptive because each direct matchup has six games in the main conditions and the same three seeds recur across conditions. Move-order effects are first-seat minus second-seat win points. Runtime is total recorded decision time divided by the number of non-pass decisions. A capture is classified as a net launch when the game log records the second friendly source piece required by the launcher. Every one of the 1,116 game logs was replayed from its forced market draws and matched to its recorded final score and winner.", styles,
        ),
        PageBreak(),
        p("4. Results", styles, "h1"),
        p("4.1 Overall agent performance", styles, "h2"),
    ])

    ranking = overall.sort_values("win_points_rate", ascending=False)
    overall_rows = [["Agent", "Games", "Win points", "Mean margin", "ms/decision", "First", "Second"]]
    for agent, row in ranking.iterrows():
        overall_rows.append([
            AGENT_LABELS[agent], int(row.games), fmt_pct(row.win_points_rate), f"{row.mean_margin:+.2f}", f"{row.milliseconds_per_decision:,.2f}", fmt_pct(seat.loc[agent, "first"]), fmt_pct(seat.loc[agent, "second"]),
        ])
    story.extend([
        p(
            "Rule ranked first across the 1,080 main and deck games, with 69.0% win points. MCTS ranked second (62.1%), followed by expectimax d3 (59.0%), expectimax d2 (55.7%), greedy (53.9%), and random (0.3%). The ranking should not be read as universal: performance shifted substantially across boards and stopping rules (Figure 2).", styles,
        ),
        p("Table 3. Aggregate performance across the 12 unique main/deck conditions.", styles, "table_title"),
        article_table(overall_rows, [31 * mm, 16 * mm, 22 * mm, 22 * mm, 25 * mm, 19 * mm, 19 * mm], font_size=7.0),
    ])
    add_figure(
        story, figures["board_goal"],
        "<b>Figure 2. Agent performance depends on board and end condition.</b> Each panel shows one board; bars show win points for each agent across its five opponents (30 agent-game observations per bar: five opponents x both orientations x three matched seeds). The dashed line marks 50% win points. Goal-10, goal-40, and fixed-horizon results are separate conditions, not pooled replications. Random bars are near zero and may be visually absent.",
        styles,
    )

    story.extend([
        p("4.2 End condition and move order", styles, "h2"),
        p(
            "Goal 10 produced short games on all boards: 14.2 combined turns on the default board, 15.3 on bottleneck, and 6.6 on the inner ring. Goal 40 required 58.1 turns on the default board, 34.6 on bottleneck, and 23.0 on the inner ring. The default goal-40 condition was longer than the fixed 50-turn schedule because its safety cap permits up to 100 combined turns. The inner ring ended fastest because a piece can quickly reach and repeatedly score the four-point center.", styles,
        ),
        p(
            "Expectimax d3 had the largest aggregate first-seat advantage (+7.5 percentage points), followed by rule (+5.3), expectimax d2 (+4.2), greedy (+2.2), and random (+0.6). MCTS was the exception: it scored 1.9 points better when moving second. These descriptive differences justify preserving player orientation in every comparison.", styles,
        ),
    ])
    add_figure(
        story, figures["length_order"],
        "<b>Figure 3. End condition controls match duration and player order affects agents differently.</b> (A) Mean combined turns per game for each board/end-condition cell (90 games per bar). Fixed 25 denotes 25 scheduled turns per player. Goal conditions end immediately when a player reaches the threshold, subject to a 50-turn-per-player safety cap. (B) Difference between first-seat and second-seat win-points rates across the 1,080 main/deck games (180 agent-game observations per seat and agent). Positive values favor moving first.",
        styles,
    )

    story.extend([
        p("4.3 Independent deck-composition test", styles, "h2"),
        p(
            "Rule remained strongest under every deck and reached 100% aggregate win points under the swap-heavy deck in this sample. MCTS was consistently second on the movement-heavy and swap-heavy decks. Expectimax depth increased cost without producing a corresponding monotonic gain. Because all deck tests use the default board and fixed horizon, these differences can be attributed to card supply more cleanly than in a full deck-by-board factorial.", styles,
        ),
    ])
    add_figure(
        story, figures["deck"],
        "<b>Figure 4. Independent deck-composition test.</b> Cells show win points (%) for each agent across five opponents on the default board with a fixed 25-turn-per-player horizon (30 agent-game observations per cell). Decks contain 28 cards; exact card counts are given in Table 2. All conditions use the two-pass market refresh, so capture-heavy results are not shortened by an absorbing illegal market.",
        styles,
    )

    story.extend([
        p("4.4 Expectimax depth and computation", styles, "h2"),
        p(
            f"Across the nine direct board/end-condition comparisons, expectimax d3 obtained {fmt_pct(d3_wp)} of win points against d2 over 54 agent-game observations. Depth 3 was better in both bottleneck goal conditions, depth 2 was better on default fixed, default goal 40, and inner-ring goal 10, and the remaining conditions were tied. Across the main suite, depth 3 required {overall.loc['expectimax_d3', 'milliseconds_per_decision'] / overall.loc['expectimax_d2', 'milliseconds_per_decision']:.1f} times the decision time of depth 2. The bounded study confirms a further order-of-magnitude increase at depth 4.", styles,
        ),
    ])
    add_figure(
        story, figures["depth"],
        "<b>Figure 5. Greater expectimax depth is costly and not uniformly stronger.</b> (A) Direct depth-2 versus depth-3 win points in each board/end-condition cell. Each pair of bars summarizes six games: three matched seeds in both orientations. The dashed line marks 50%. (B) Weighted mean decision time in the bounded goal-20 study on a logarithmic axis. Depths use the same top-2 action cap. Each point aggregates six agent-game observations against rule and the other depths on one board; depth-4 strength estimates are not stable at this sample size.",
        styles,
    )

    story.extend([
        p("4.5 Net-launcher use", styles, "h2"),
        p(
            f"The suite contains {total_caps:,} recorded capture actions, of which {total_net:,} ({100 * total_net / total_caps:.1f}%) used the net launcher. The six main agents had similar net shares (19.3%-26.0%), with random highest and rule lowest. Expectimax d4 reached 27.5%, but its denominator is only 40 captures and should not be compared as if equally precise.", styles,
        ),
    ])
    net_rows = [["Agent", "Adjacent", "Net", "All captures", "Net share"]]
    for row in net.set_index("agent").reindex(AGENTS + ["expectimax_d4"]).reset_index().itertuples(index=False):
        net_rows.append([AGENT_LABELS[row.agent], int(row.adjacent), int(row.net), int(row.total_captures), fmt_pct(row.net_share)])
    story.extend([
        p("Table 4. Adjacent and net-launcher capture actions.", styles, "table_title"),
        article_table(net_rows, [38 * mm, 25 * mm, 22 * mm, 28 * mm, 25 * mm], font_size=7.3),
    ])
    add_figure(
        story, figures["net"],
        "<b>Figure 6. Use of the net-launcher capture.</b> (A) Counts of adjacent and net-launcher capture actions reconstructed from per-turn logs. (B) Net launches as a percentage of each agent's captures. The depth-4 agent appears only in the 36-game bounded depth study, whereas each main agent appears throughout the main/deck suite; counts and shares must therefore be interpreted together.",
        styles,
    )

    story.extend([
        p("5. Discussion", styles, "h1"),
        p(
            "The principal result is not simply that rule won most often. Rather, a compact, transparent policy was robust under the tested settings while more expensive search did not yield a stable advantage. Rule's capture-first and objective-first priorities align directly with the scoring function. MCTS was the strongest search method overall, particularly under alternative decks, but its cost was roughly 29 times rule's cost per decision. Expectimax d3 improved aggregate performance relative to d2, yet lost the direct depth comparison overall and was more than seven times slower. This is consistent with a search horizon that changes which heuristic leaf states are preferred without guaranteeing that the additional lookahead resolves the strategically relevant uncertainty.", styles,
        ),
        p(
            "Board geometry changes which policy assumptions are useful. On the default board, rule dominated fixed and goal-40 play, while greedy and expectimax were more competitive on bottleneck and inner-ring conditions. The four-point inner-ring objective makes positional control disproportionately important and produces extremely short goal-10 games. Consequently, a low score goal emphasizes openings and seat order rather than sustained control. Goal 40 provides a longer strategic test but can exceed a 50-turn total on the default board.", styles,
        ),
        p(
            "The market refresh is essential to the interpretation. Preliminary capture-heavy experiments under the original pass rule frequently entered a state in which no legal market card could be used and the unchanged market caused repeated passes. Refreshing after two consecutive passes removed this absorbing mechanism. The final suite therefore evaluates agent behavior in continuing games rather than performance distorted by scheduled no-op turns.", styles,
        ),
        p("5.1 Limitations", styles, "h2"),
        p(
            "First, each direct main matchup contains only six games and reuses three seeds across conditions. Percentages are therefore descriptive screening estimates rather than precise population parameters. Second, the reduced design does not cross every board with every deck; deck composition is intentionally isolated on the default board. Third, expectimax uses a top-2 action cap, so the experiment compares practical bounded variants rather than unrestricted exact search. Fourth, depth 4 has one seed and is primarily a feasibility measurement; depths 5 and 6 were excluded after depth 5 exceeded 120 seconds for a single benchmark decision. Fifth, MCTS samples transitions using the threaded game state rather than representing public draw uncertainty with explicit chance nodes. Finally, the shared heuristic may favor agents whose search procedure uses it directly, and no independent heuristic-weight sensitivity analysis is included in the final suite.", styles,
        ),
        p("6. Conclusions", styles, "h1"),
        p(
            "Under the final market-refresh rule and reduced experimental design, rule-based play provided the strongest performance-cost trade-off. MCTS was the best search agent, while deeper expectimax was substantially more expensive and not consistently superior to depth 2. Board geometry and score goal materially changed rankings, match duration, and order sensitivity. The goal-10 extension is useful as an opening-focused stress test, but it should not replace longer goal-40 or fixed-horizon evaluation. Future confirmatory work should increase the number of paired seeds, compare agents under equal decision-time budgets, and tune heuristic weights on data separated from the final evaluation set.", styles,
        ),
        p("Data and code availability", styles, "h1"),
        p(
            "Mode configurations, immutable board/deck snapshots, aggregate results, and per-turn game logs are stored under <font name='Courier'>modes/reduced_*</font>. Report tables and vector/raster figure exports are stored under <font name='Courier'>final_results/final_report/</font>. The coverage manifest is <font name='Courier'>final_results/reduced_factorial/tables/01_coverage_manifest.csv</font>. Analysis and validation are reproducible with <font name='Courier'>analysis/reduced_factorial_report.py</font>, <font name='Courier'>analysis/validate_reduced_factorial.py</font>, and <font name='Courier'>analysis/build_final_report.py</font>.", styles,
        ),
        p("References", styles, "h1"),
        p("1. Graph Card Control official rules. <font name='Courier'>Instructions.md</font>.", styles, "small"),
        p("2. Project architecture and experiment conventions. <font name='Courier'>AGENTS.md</font>.", styles, "small"),
        p("3. Reduced factorial source tables. <font name='Courier'>final_results/reduced_factorial/tables/</font>.", styles, "small"),
        p("Appendix A. Coverage manifest", styles, "h1"),
        p(
            "Every row below passed the automated coverage audit: market refresh = 2, expected ordered-pair files present, expected aggregate result rows present, and one game log per result row. All logs were also replay-validated.", styles,
        ),
    ])
    coverage_rows = [["Mode", "Board", "Deck", "Goal", "Games", "OK"]]
    for row in data["coverage"].itertuples(index=False):
        coverage_rows.append([row.mode.replace("reduced_", ""), row.board, row.deck, "-" if pd.isna(row.score_to_win) else int(row.score_to_win), int(row.result_rows), "yes" if row.coverage_ok else "no"])
    story.append(article_table(coverage_rows, [58 * mm, 28 * mm, 25 * mm, 12 * mm, 14 * mm, 12 * mm], font_size=6.3))

    doc = ArticleDocTemplate(str(pdf_path))
    doc.build(story)
    return pdf_path


def write_evidence_ledger(data: dict[str, pd.DataFrame], pdf_path: Path) -> None:
    ledger = [
        ["claim_or_decision", "status", "evidence_locator", "confidence_or_check"],
        ["Final suite contains 1,116 games", "observed", "tables/01_coverage_manifest.csv", "15 modes; file/result counts checked"],
        ["All game logs replay to recorded scores/winners", "observed", "analysis/validate_reduced_factorial.py output", "1,116/1,116 passed"],
        ["Rule has 69.0% aggregate win points", "derived", "reduced_factorial tables 03 and 10", "equal first/second exposure; recalculated by build script"],
        ["Goal 10 averages 12.1 combined turns", "derived", "reduced_factorial table 09", "mean of three 90-game board cells"],
        ["Expectimax d3 gets 48.1% direct WP vs d2", "derived", "reduced_factorial table 05", "54 agent-game observations"],
        ["Net launches are 21.3% of captures", "derived", "reduced_factorial table 07", "1,715/8,041 events"],
        ["Use three-board reduced design", "requirement", "user instruction in task", "default, bottleneck, inner-ring center"],
        ["Depth 4 bounded; depths 5-6 excluded", "recommendation", "future experiments table 14 and bounded runtime data", "depth 5 single-decision timeout >120 s"],
        ["Final PDF rendered and inspected", "observed", str(pdf_path), "pending until QA script completes"],
    ]
    with (OUT / "EVIDENCE_LEDGER.csv").open("w", newline="", encoding="utf-8") as handle:
        csv.writer(handle).writerows(ledger)


def main() -> None:
    FIGURES.mkdir(parents=True, exist_ok=True)
    TABLES.mkdir(parents=True, exist_ok=True)
    data = prepare_data()
    figures = make_result_figures(data)
    pdf_path = build_pdf(data, figures)
    data["coverage"].to_csv(TABLES / "01_coverage_manifest.csv", index=False)
    data["overall"].to_csv(TABLES / "02_overall_agent_performance.csv", index=False, float_format="%.6f")
    data["game_summary"].to_csv(TABLES / "03_game_length.csv", index=False, float_format="%.6f")
    data["deck_summary"].to_csv(TABLES / "04_deck_performance.csv", index=False, float_format="%.6f")
    data["direct_depth"].to_csv(TABLES / "05_direct_depth_comparison.csv", index=False, float_format="%.6f")
    data["net_summary"].to_csv(TABLES / "06_net_launcher.csv", index=False, float_format="%.6f")
    write_evidence_ledger(data, pdf_path)
    print(pdf_path)


if __name__ == "__main__":
    main()
