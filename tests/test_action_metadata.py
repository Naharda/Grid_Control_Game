from __future__ import annotations

from game.cards import CardType
from game.rules import apply_action, get_legal_actions
from game.state import initial_state


def _capture_only_state(positions_a, positions_b, config=None):
    state = initial_state(config)
    return state.with_updates(
        positions={"A": tuple(positions_a), "B": tuple(positions_b)},
        market=(CardType.CAPTURE,),
    )


def test_base_capture_records_the_acting_piece() -> None:
    state = _capture_only_state([(2, 2), (0, 0), (0, 4)], [(2, 3), (4, 0), (4, 4)])
    captures = [a for a in get_legal_actions(state) if a.mode == "base"]
    assert captures
    for action in captures:
        assert len(action.moves) == 1
        assert action.moves[0].to_pos == state.positions["A"][action.moves[0].piece_id]
        assert action.launcher_id is None
    assert {a.moves[0].piece_id for a in captures} == {0}


def test_base_capture_lists_every_adjacent_actor() -> None:
    state = _capture_only_state([(2, 2), (2, 4), (0, 0)], [(2, 3), (4, 0), (4, 4)])
    captures = [a for a in get_legal_actions(state) if a.mode == "base"]
    assert {(a.moves[0].piece_id, a.target_piece) for a in captures} == {
        (0, ("B", 0)),
        (1, ("B", 0)),
    }


def test_net_capture_records_launched_and_launcher_pieces() -> None:
    state = _capture_only_state([(2, 1), (2, 2), (0, 0)], [(2, 4), (4, 0), (4, 4)])
    nets = [a for a in get_legal_actions(state) if a.mode == "net"]
    assert nets
    for action in nets:
        assert action.target_piece == ("B", 0)
        assert len(action.moves) == 1
    # The ray toward (2, 4) fires rightward: launched piece is A1 at (2, 2),
    # its adjacent partner A0 at (2, 1) is the launcher.
    assert {(a.moves[0].piece_id, a.launcher_id) for a in nets} == {(1, 0)}


def test_capture_moves_are_noops_when_applied() -> None:
    state = _capture_only_state([(1, 2), (0, 0), (0, 4)], [(1, 3), (4, 0), (4, 4)])
    action = next(a for a in get_legal_actions(state) if a.mode == "base")
    nxt = apply_action(state, action)
    assert nxt.positions["A"] == state.positions["A"]
    assert nxt.positions["B"][0] != state.positions["B"][0]
    assert nxt.scores["A"] == state.config.capture_score
