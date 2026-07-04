from __future__ import annotations

from game.cards import CardType
from game.config import GameConfig
from game.rules import apply_action, get_legal_actions
from game.state import initial_state


def _capture_only_state(positions_a, positions_b, config=None):
    state = initial_state(config)
    return state.with_updates(
        positions={"A": tuple(positions_a), "B": tuple(positions_b)},
        market=(CardType.CAPTURE,),
    )


def test_initial_state_has_legal_actions() -> None:
    state = initial_state()
    actions = get_legal_actions(state)
    assert actions
    assert len(state.market) == state.config.market_size


def test_apply_action_switches_player_and_replaces_card() -> None:
    state = initial_state()
    action = get_legal_actions(state)[0]
    nxt = apply_action(state, action)
    assert nxt.current_player == "B"
    assert nxt.turn_counts["A"] == 1
    assert len(nxt.market) == state.config.market_size


def test_capture_card_can_be_detected_in_market() -> None:
    state = initial_state()
    assert any(card in set(CardType) for card in state.market)


def test_net_capture_from_adjacent_pair_skips_empty_cells() -> None:
    state = _capture_only_state([(2, 1), (2, 2), (0, 0)], [(2, 4), (4, 0), (4, 4)])
    nets = [a for a in get_legal_actions(state) if a.mode == "net"]
    assert nets
    assert {a.target_piece for a in nets} == {("B", 0)}


def test_aligned_but_not_adjacent_pair_cannot_net_capture() -> None:
    state = _capture_only_state([(2, 0), (2, 2), (0, 0)], [(2, 4), (4, 0), (4, 4)])
    captures = [a for a in get_legal_actions(state) if a.card_type == CardType.CAPTURE]
    assert not captures


def test_net_capture_stops_at_first_enemy_piece() -> None:
    state = _capture_only_state([(2, 0), (2, 1), (0, 0)], [(2, 3), (2, 4), (4, 0)])
    nets = [a for a in get_legal_actions(state) if a.mode == "net"]
    assert nets
    assert {a.target_piece for a in nets} == {("B", 0)}


def test_net_capture_range_is_limited() -> None:
    config = GameConfig(board_size=(5, 7))
    state = _capture_only_state([(2, 0), (2, 1), (0, 0)], [(2, 5), (4, 0), (4, 6)], config)
    captures = [a for a in get_legal_actions(state) if a.card_type == CardType.CAPTURE]
    assert not captures


def test_melee_capture_of_adjacent_enemy() -> None:
    state = _capture_only_state([(2, 2), (0, 0), (0, 4)], [(2, 3), (4, 0), (4, 4)])
    captures = [a for a in get_legal_actions(state) if a.card_type == CardType.CAPTURE]
    assert captures
    assert all(a.mode == "base" for a in captures)
    assert {a.target_piece for a in captures} == {("B", 0)}
