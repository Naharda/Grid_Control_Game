from __future__ import annotations

from game.cards import CardType
from game.config import GameConfig
from game.engine import play_match
from game.rules import apply_action, apply_pass, get_legal_actions
from game.state import initial_state
from agents.random_agent import RandomAgent


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


def test_market_refreshes_after_two_consecutive_passes() -> None:
    config = GameConfig(seed=1, market_refresh_after_passes=2)
    state = initial_state(config).with_updates(
        positions={"A": ((0, 0), (0, 1), (0, 2)), "B": ((4, 2), (4, 3), (4, 4))},
        market=(CardType.CAPTURE, CardType.CAPTURE, CardType.CAPTURE),
    )
    original_market = state.market

    after_one = apply_pass(state)
    assert after_one.market == original_market
    assert after_one.consecutive_passes == 1

    after_two = apply_pass(after_one)
    assert after_two.market != original_market
    assert len(after_two.market) == config.market_size
    assert after_two.consecutive_passes == 0
    assert after_two.last_action == "pass+market_refresh"


def test_legal_action_resets_consecutive_pass_counter() -> None:
    state = initial_state().with_updates(consecutive_passes=1)
    nxt = apply_action(state, get_legal_actions(state)[0])
    assert nxt.consecutive_passes == 0


def test_market_refresh_conserves_cards() -> None:
    config = GameConfig(
        turns_per_player=3,
        market_refresh_after_passes=2,
        deck_composition={CardType.CAPTURE: 5},
    )
    total = sum(config.deck_composition.values())
    observed_refresh = False

    def check(before, action, after):
        nonlocal observed_refresh
        assert len(after.market) + len(after.deck) + len(after.discard) == total
        observed_refresh |= after.last_action == "pass+market_refresh"

    play_match(
        RandomAgent(seed=0),
        RandomAgent(seed=1),
        initial_state(config),
        on_step=check,
    )
    assert observed_refresh


def test_score_goal_ends_game_immediately() -> None:
    config = GameConfig(score_to_win=1)
    state = initial_state(config).with_updates(
        positions={"A": ((2, 1), (0, 0), (0, 4)), "B": ((4, 1), (4, 2), (4, 3))},
        market=(CardType.MOVE1,),
    )
    action = next(
        action
        for action in get_legal_actions(state)
        if action.moves[0].to_pos == config.center
    )
    after = apply_action(state, action)
    assert after.scores["A"] == 1
    assert after.is_terminal
    assert after.turn_counts["A"] == 1


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
