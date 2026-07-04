from __future__ import annotations

import json

import pytest

from game.config import GameConfig
from game.setup_loader import (
    build_config,
    deck_config_kwargs,
    load_board,
    load_deck,
    validate_board,
    validate_deck,
)


def _default_board() -> dict:
    return json.loads(json.dumps(load_board("default")))


def _default_deck() -> dict:
    return json.loads(json.dumps(load_deck("default")))


def test_default_files_reproduce_default_config() -> None:
    config = build_config(board=load_board("default"), deck=load_deck("default"), seed=1)
    default = GameConfig()
    assert config.board_size == default.board_size
    assert config.pieces_per_player == default.pieces_per_player
    assert config.player_a_spawns == default.player_a_spawns
    assert config.player_b_spawns == default.player_b_spawns
    assert config.scoring_cells == default.scoring_cells
    assert config.blocked_cells == default.blocked_cells
    assert config.deck_composition == default.deck_composition
    assert config.market_size == default.market_size
    assert config.seed == default.seed


def test_build_config_accepts_rule_overrides() -> None:
    config = build_config(board=load_board("default"), deck=load_deck("default"), seed=5, turns_per_player=10)
    assert config.seed == 5
    assert config.turns_per_player == 10


def test_missing_board_lists_available_names() -> None:
    with pytest.raises(FileNotFoundError, match="default"):
        load_board("no-such-board")


def test_unknown_card_name_rejected() -> None:
    deck = _default_deck()
    deck["cards"]["teleport"] = 2
    with pytest.raises(ValueError, match="teleport"):
        validate_deck(deck)


def test_non_positive_card_count_rejected() -> None:
    deck = _default_deck()
    deck["cards"]["move1"] = 0
    with pytest.raises(ValueError, match="move1"):
        validate_deck(deck)


def test_spawn_out_of_bounds_rejected() -> None:
    board = _default_board()
    board["spawns"]["A"][0] = [9, 0]
    with pytest.raises(ValueError, match="out of bounds"):
        validate_board(board)


def test_spawn_on_blocked_cell_rejected() -> None:
    board = _default_board()
    board["blocked_cells"] = [[0, 1]]
    with pytest.raises(ValueError, match="blocked"):
        validate_board(board)


def test_mismatched_spawn_counts_rejected() -> None:
    board = _default_board()
    board["spawns"]["B"] = board["spawns"]["B"][:2]
    with pytest.raises(ValueError, match="same number"):
        validate_board(board)


def test_capture_cell_out_of_bounds_rejected() -> None:
    board = _default_board()
    board["capture_cells"] = [{"cell": [5, 5], "points": 1}]
    with pytest.raises(ValueError, match="out of bounds"):
        validate_board(board)


def test_capture_cell_points_must_be_positive() -> None:
    board = _default_board()
    board["capture_cells"] = [{"cell": [2, 2], "points": 0}]
    with pytest.raises(ValueError, match="points"):
        validate_board(board)


def test_deck_smaller_than_market_rejected() -> None:
    deck = _default_deck()
    deck["cards"] = {"move1": 2}
    with pytest.raises(ValueError, match="market_size"):
        build_config(deck=deck)


def test_deck_kwargs_parse_card_names() -> None:
    kwargs = deck_config_kwargs(_default_deck())
    assert sum(kwargs["deck_composition"].values()) == 28
