from __future__ import annotations

from game.actions import Action, PieceMove
from game.cards import CardType
from game.config import GameConfig
from game.rules import apply_action, get_legal_actions
from game.state import initial_state


def _move_only_state(positions_a, positions_b, config=None):
    state = initial_state(config)
    return state.with_updates(
        positions={"A": tuple(positions_a), "B": tuple(positions_b)},
        market=(CardType.MOVE1,),
    )


def test_default_scoring_cells_match_legacy_center() -> None:
    assert GameConfig().scoring_cells == {(2, 2): 1}
    assert GameConfig(board_size=(5, 7)).scoring_cells == {(2, 3): 1}
    assert GameConfig(center_score=4).scoring_cells == {(2, 2): 4}


def test_explicit_capture_cells_override_center() -> None:
    config = GameConfig(capture_cells={(0, 0): 2, (4, 4): 5})
    assert config.scoring_cells == {(0, 0): 2, (4, 4): 5}
    assert (2, 2) not in config.scoring_cells


def test_each_occupied_capture_cell_scores_every_turn() -> None:
    config = GameConfig(capture_cells={(1, 1): 2, (1, 3): 5})
    state = _move_only_state([(1, 1), (1, 3), (3, 0)], [(4, 1), (4, 2), (4, 3)], config)
    action = Action(0, CardType.MOVE1, moves=(PieceMove(2, (2, 0)),))
    nxt = apply_action(state, action)
    assert nxt.scores["A"] == 7
    assert nxt.scores["B"] == 0


def test_capture_cells_only_score_for_the_mover() -> None:
    config = GameConfig(capture_cells={(1, 1): 2})
    state = _move_only_state([(3, 0), (0, 2), (0, 3)], [(1, 1), (4, 2), (4, 3)], config)
    action = Action(0, CardType.MOVE1, moves=(PieceMove(0, (2, 0)),))
    nxt = apply_action(state, action)
    assert nxt.scores == {"A": 0, "B": 0}


def test_blocked_cells_are_impassable() -> None:
    config = GameConfig(blocked_cells=((2, 0),))
    state = _move_only_state([(1, 0), (0, 2), (0, 3)], [(4, 1), (4, 2), (4, 3)], config)
    assert (2, 0) not in state.board.positions
    destinations = {a.moves[0].to_pos for a in get_legal_actions(state) if a.moves[0].piece_id == 0}
    assert (2, 0) not in destinations


def test_blocked_cell_stops_net_ray() -> None:
    config = GameConfig(blocked_cells=((2, 3),))
    state = initial_state(config).with_updates(
        positions={"A": ((2, 1), (2, 2), (0, 0)), "B": ((2, 4), (4, 0), (4, 4))},
        market=(CardType.CAPTURE,),
    )
    nets = [a for a in get_legal_actions(state) if a.mode == "net"]
    assert not nets


def test_captured_piece_never_respawns_on_blocked_cell() -> None:
    config = GameConfig(blocked_cells=((0, 1), (0, 2)))
    state = initial_state(config).with_updates(
        positions={"A": ((3, 1), (0, 3), (1, 2)), "B": ((3, 2), (0, 0), (1, 1))},
        market=(CardType.CAPTURE,),
    )
    captures = [a for a in get_legal_actions(state) if a.target_piece == ("B", 0)]
    assert captures
    nxt = apply_action(state, captures[0])
    respawned = nxt.positions["B"][0]
    assert respawned not in config.blocked_cells
    assert nxt.board.in_bounds(respawned)
