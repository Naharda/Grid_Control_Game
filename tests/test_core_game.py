from __future__ import annotations

from game.cards import CardType
from game.rules import apply_action, get_legal_actions
from game.state import initial_state


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
