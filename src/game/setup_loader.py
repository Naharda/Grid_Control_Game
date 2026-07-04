"""Load board and deck definitions from JSON files into GameConfig kwargs.

Boards live in `boards/<name>.json`, decks in `decks/<name>.json` at the repo
root. All JSON coordinates are engine-native `[row, col]`, 0-based.
"""

from __future__ import annotations

import json
from pathlib import Path

from .cards import card_from_value
from .config import GameConfig

REPO_ROOT = Path(__file__).resolve().parents[2]
BOARDS_DIR = REPO_ROOT / "boards"
DECKS_DIR = REPO_ROOT / "decks"


def resolve_data_path(name_or_path: str | Path, directory: Path, kind: str) -> Path:
    path = Path(name_or_path)
    if path.suffix == ".json" and (path.is_absolute() or path.exists()):
        return path
    path = directory / f"{name_or_path}.json"
    if not path.exists():
        available = sorted(p.stem for p in directory.glob("*.json")) if directory.exists() else []
        raise FileNotFoundError(f"No {kind} named {name_or_path!r} ({path}); available: {available}")
    return path


def _load_json(path: Path, kind: str) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {kind} file {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"{kind} file {path} must contain a JSON object")
    return data


def _cell(value, context: str) -> tuple[int, int]:
    if not (isinstance(value, (list, tuple)) and len(value) == 2 and all(isinstance(v, int) for v in value)):
        raise ValueError(f"{context}: expected a [row, col] pair, got {value!r}")
    return (value[0], value[1])


def load_board(name_or_path: str | Path, *, boards_dir: Path | None = None) -> dict:
    path = resolve_data_path(name_or_path, boards_dir or BOARDS_DIR, "board")
    board = _load_json(path, "board")
    validate_board(board, source=str(path))
    return board


def validate_board(board: dict, source: str = "<board>") -> None:
    rows, cols = board.get("rows"), board.get("cols")
    if not (isinstance(rows, int) and isinstance(cols, int) and rows >= 1 and cols >= 1):
        raise ValueError(f"{source}: 'rows' and 'cols' must be positive integers")

    def in_bounds(cell: tuple[int, int]) -> bool:
        return 0 <= cell[0] < rows and 0 <= cell[1] < cols

    blocked = {_cell(c, f"{source}: blocked_cells") for c in board.get("blocked_cells", [])}
    for cell in blocked:
        if not in_bounds(cell):
            raise ValueError(f"{source}: blocked cell {cell} is out of bounds")

    spawns = board.get("spawns")
    if not (isinstance(spawns, dict) and set(spawns) == {"A", "B"}):
        raise ValueError(f"{source}: 'spawns' must be an object with exactly the keys 'A' and 'B'")
    parsed_spawns = {}
    for player, cells in spawns.items():
        parsed = [_cell(c, f"{source}: spawns[{player}]") for c in cells]
        if not parsed:
            raise ValueError(f"{source}: spawns[{player}] must not be empty")
        if len(set(parsed)) != len(parsed):
            raise ValueError(f"{source}: spawns[{player}] contains duplicate cells")
        for cell in parsed:
            if not in_bounds(cell):
                raise ValueError(f"{source}: spawn {cell} for player {player} is out of bounds")
            if cell in blocked:
                raise ValueError(f"{source}: spawn {cell} for player {player} is on a blocked cell")
        parsed_spawns[player] = parsed
    if len(parsed_spawns["A"]) != len(parsed_spawns["B"]):
        raise ValueError(f"{source}: players must have the same number of spawn cells")
    if set(parsed_spawns["A"]) & set(parsed_spawns["B"]):
        raise ValueError(f"{source}: players share a spawn cell")
    declared = board.get("pieces_per_player")
    if declared is not None and declared != len(parsed_spawns["A"]):
        raise ValueError(f"{source}: pieces_per_player={declared} does not match {len(parsed_spawns['A'])} spawns")

    capture_cells = board.get("capture_cells")
    if not isinstance(capture_cells, list) or not capture_cells:
        raise ValueError(f"{source}: 'capture_cells' must be a non-empty list")
    seen: set[tuple[int, int]] = set()
    for entry in capture_cells:
        if not (isinstance(entry, dict) and "cell" in entry and "points" in entry):
            raise ValueError(f"{source}: each capture cell needs 'cell' and 'points', got {entry!r}")
        cell = _cell(entry["cell"], f"{source}: capture_cells")
        if not in_bounds(cell):
            raise ValueError(f"{source}: capture cell {cell} is out of bounds")
        if cell in blocked:
            raise ValueError(f"{source}: capture cell {cell} is blocked")
        if cell in seen:
            raise ValueError(f"{source}: capture cell {cell} appears twice")
        seen.add(cell)
        if not (isinstance(entry["points"], int) and entry["points"] >= 1):
            raise ValueError(f"{source}: capture cell {cell} points must be a positive integer")


def load_deck(name_or_path: str | Path, *, decks_dir: Path | None = None) -> dict:
    path = resolve_data_path(name_or_path, decks_dir or DECKS_DIR, "deck")
    deck = _load_json(path, "deck")
    validate_deck(deck, source=str(path))
    return deck


def validate_deck(deck: dict, source: str = "<deck>") -> None:
    cards = deck.get("cards")
    if not isinstance(cards, dict) or not cards:
        raise ValueError(f"{source}: 'cards' must be a non-empty object of name -> count")
    for name, count in cards.items():
        try:
            card_from_value(name)
        except ValueError as exc:
            raise ValueError(f"{source}: unknown card {name!r}") from exc
        if not (isinstance(count, int) and count >= 1):
            raise ValueError(f"{source}: card {name!r} count must be a positive integer")


def board_config_kwargs(board: dict) -> dict:
    return {
        "board_size": (board["rows"], board["cols"]),
        "pieces_per_player": len(board["spawns"]["A"]),
        "player_a_spawns": tuple(tuple(c) for c in board["spawns"]["A"]),
        "player_b_spawns": tuple(tuple(c) for c in board["spawns"]["B"]),
        "capture_cells": {tuple(e["cell"]): e["points"] for e in board["capture_cells"]},
        "blocked_cells": tuple(tuple(c) for c in board.get("blocked_cells", [])),
    }


def deck_config_kwargs(deck: dict) -> dict:
    return {"deck_composition": {card_from_value(name): count for name, count in deck["cards"].items()}}


def build_config(
    board: dict | None = None,
    deck: dict | None = None,
    seed: int | None = 1,
    **overrides,
) -> GameConfig:
    kwargs: dict = {"seed": seed}
    if board is not None:
        kwargs.update(board_config_kwargs(board))
    if deck is not None:
        kwargs.update(deck_config_kwargs(deck))
    kwargs.update(overrides)
    config = GameConfig(**kwargs)
    if sum(config.deck_composition.values()) < config.market_size:
        raise ValueError("Deck must contain at least market_size cards")
    return config
