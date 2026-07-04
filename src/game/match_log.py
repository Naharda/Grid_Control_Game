"""Per-game move logs in the games-CSV format.

Each row is a start-of-turn snapshot (scores, market as the player to act
sees it) whose action columns describe the PREVIOUS turn's move; row 0 uses
-1/"None" placeholders and a trailing row captures the final move together
with the final scores/market.

Position strings are "<col>-<row>", 0-based — note the column-first order,
the inverse of the engine's (row, col) tuples. `pos_to_str`/`parse_pos` are
the only place this inversion exists.
"""

from __future__ import annotations

import csv
from pathlib import Path

from .actions import Action
from .board import Position
from .cards import CardType, card_from_value
from .rules import apply_action, get_legal_actions
from .state import GameState

EMPTY = "-1"
NO_CARD = "None"


def pos_to_str(pos: Position | None) -> str:
    if pos is None:
        return EMPTY
    return f"{pos[1]}-{pos[0]}"


def parse_pos(text: str) -> Position | None:
    if text == EMPTY:
        return None
    col, row = text.split("-")
    return (int(row), int(col))


def games_csv_header(market_size: int) -> list[str]:
    return (
        ["turn", "player", "score_a", "score_b"]
        + [f"card_{i}" for i in range(market_size)]
        + ["action", "card_drawn", "src_0", "dst_0", "src_1", "dst_1"]
    )


def action_columns(before: GameState, action: Action | None) -> dict[str, object]:
    """src/dst columns for `action` taken from state `before` (excluding card_drawn)."""
    if action is None:
        return {"action": -1, "src_0": EMPTY, "dst_0": EMPTY, "src_1": EMPTY, "dst_1": EMPTY}

    player = before.current_player
    cols: dict[str, object] = {"action": action.card_index, "src_0": EMPTY, "dst_0": EMPTY, "src_1": EMPTY, "dst_1": EMPTY}

    def origin(move_idx: int) -> Position:
        return before.positions[player][action.moves[move_idx].piece_id]

    if action.card_type in (CardType.MOVE1, CardType.MOVE2):
        cols["src_0"] = pos_to_str(origin(0))
        cols["dst_0"] = pos_to_str(action.moves[0].to_pos)
    elif action.card_type == CardType.MOBILIZE:
        cols["src_0"] = pos_to_str(origin(0))
        cols["dst_0"] = pos_to_str(action.moves[0].to_pos)
        if len(action.moves) > 1:
            cols["src_1"] = pos_to_str(origin(1))
            cols["dst_1"] = pos_to_str(action.moves[1].to_pos)
    elif action.card_type == CardType.CAPTURE:
        target_player, target_idx = action.target_piece
        cols["src_0"] = pos_to_str(origin(0))
        cols["dst_0"] = pos_to_str(before.positions[target_player][target_idx])
        if action.mode == "net":
            cols["src_1"] = pos_to_str(before.positions[player][action.launcher_id])
    elif action.card_type == CardType.SWAP:
        target_player, target_idx = action.swap_piece
        cols["src_0"] = pos_to_str(origin(0))
        cols["dst_0"] = pos_to_str(before.positions[target_player][target_idx])
    return cols


class GameCsvRecorder:
    """Collects games-CSV rows from (before, action, after) steps.

    Plug `record_step` into `engine.play_match(on_step=...)`, then call
    `finalize()` to obtain the rows including the trailing snapshot.
    """

    def __init__(self, market_size: int) -> None:
        self.market_size = market_size
        self.rows: list[dict] = []
        self._turn = 0
        self._prev_action_cols: dict[str, object] = dict(action_columns(None, None), card_drawn=NO_CARD)
        self._last_after: GameState | None = None

    def record_step(self, before: GameState, action: Action | None, after: GameState) -> None:
        self.rows.append(self._snapshot(before) | self._prev_action_cols)
        self._turn += 1
        cols = dict(action_columns(before, action))
        if action is None:
            cols["card_drawn"] = NO_CARD
        elif len(after.market) == len(before.market):
            cols["card_drawn"] = after.market[action.card_index].value
        else:
            cols["card_drawn"] = NO_CARD
        self._prev_action_cols = cols
        self._last_after = after

    def finalize(self) -> list[dict]:
        if self._last_after is not None:
            self.rows.append(self._snapshot(self._last_after) | self._prev_action_cols)
            self._last_after = None
        return self.rows

    def _snapshot(self, state: GameState) -> dict[str, object]:
        row: dict[str, object] = {
            "turn": self._turn,
            "player": 0 if state.current_player == "A" else 1,
            "score_a": state.scores["A"],
            "score_b": state.scores["B"],
        }
        for i in range(self.market_size):
            row[f"card_{i}"] = state.market[i].value if i < len(state.market) else NO_CARD
        return row


def rows_from_history(history: list[GameState], actions: list[Action | None], market_size: int) -> list[dict]:
    """Build games-CSV rows from a viewer-style (history, actions) pair."""
    recorder = GameCsvRecorder(market_size)
    for before, action, after in zip(history, actions, history[1:]):
        recorder.record_step(before, action, after)
    return recorder.finalize()


def write_game_csv(path: Path, rows: list[dict], market_size: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=games_csv_header(market_size))
        writer.writeheader()
        writer.writerows(rows)


def read_game_csv(path: Path) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def parse_card(text: str) -> CardType | None:
    return None if text == NO_CARD else card_from_value(text)


class ReplayError(ValueError):
    pass


def replay_rows(initial: GameState, rows: list[dict], validate: bool = True) -> list[GameState]:
    """Rebuild the state trajectory recorded by GameCsvRecorder.

    Returns one state per row: `states[t]` is the state row `t` snapshots.
    With `validate`, every snapshot column is checked against the replayed
    state and mismatches raise ReplayError naming the row and column.
    """
    states = [initial]
    state = initial
    if validate and rows:
        _validate_snapshot(rows[0], state, 0)
    for turn, row in enumerate(rows[1:], start=1):
        slot = int(row["action"])
        if slot == -1:
            if validate and get_legal_actions(state):
                raise ReplayError(f"row {turn}: recorded a pass but legal actions exist")
            state = state.with_updates(
                current_player="B" if state.current_player == "A" else "A",
                turn_counts={**state.turn_counts, state.current_player: state.turn_counts[state.current_player] + 1},
                last_action="pass",
            )
        else:
            action = _resolve_action(state, row, turn)
            state = apply_action(state, action, draw_card=parse_card(row["card_drawn"]))
        states.append(state)
        if validate:
            _validate_snapshot(row, state, turn)
    return states


def _resolve_action(state: GameState, row: dict, turn: int) -> Action:
    slot = int(row["action"])
    want = {key: row[key] for key in ("src_0", "dst_0", "src_1", "dst_1")}
    for action in get_legal_actions(state):
        if action.card_index != slot:
            continue
        cols = action_columns(state, action)
        if all(cols[key] == want[key] for key in want):
            return action
    raise ReplayError(f"row {turn}: no legal action matches slot {slot} with {want}")


def _validate_snapshot(row: dict, state: GameState, turn: int) -> None:
    expected = {
        "turn": turn,
        "player": 0 if state.current_player == "A" else 1,
        "score_a": state.scores["A"],
        "score_b": state.scores["B"],
    }
    for key, value in expected.items():
        if int(row[key]) != value:
            raise ReplayError(f"row {turn}: {key} is {row[key]}, replay produced {value}")
    market_keys = sorted(
        (key for key in row if key.startswith("card_") and key != "card_drawn"),
        key=lambda key: int(key.split("_")[1]),
    )
    for i, key in enumerate(market_keys):
        value = state.market[i].value if i < len(state.market) else NO_CARD
        if row[key] != value:
            raise ReplayError(f"row {turn}: {key} is {row[key]}, replay produced {value}")
