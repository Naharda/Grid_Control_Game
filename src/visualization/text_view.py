from __future__ import annotations

from game.cards import CARD_LABELS
from game.state import GameState


def render_state(state: GameState) -> str:
    occupied = state.occupied()
    rows: list[str] = []
    for r in range(state.board.rows):
        cells: list[str] = []
        for c in range(state.board.cols):
            pos = (r, c)
            occupant = occupied.get(pos)
            if occupant:
                player, idx = occupant
                cells.append(f"{player}{idx}")
            elif pos == state.config.center:
                cells.append("C ")
            else:
                cells.append(". ")
        rows.append(" ".join(cells))
    market = ", ".join(CARD_LABELS[c] for c in state.market)
    lines = rows + [
        f"Visible cards: [{market}]",
        f"Score: A={state.scores['A']}, B={state.scores['B']}",
        f"Turn: {state.current_player}, round {state.round_number}",
    ]
    if state.last_action:
        lines.append(f"Last action: {state.last_action}")
    return "\n".join(lines)
