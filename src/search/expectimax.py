from __future__ import annotations

from game.actions import Action
from game.rules import apply_action, get_legal_actions, possible_draws
from game.state import GameState
from search.chance import public_ordering_successor
from search.heuristic import evaluate_state
from search.minimax import SearchStats


def choose_expectimax(
    state: GameState,
    depth: int,
    player: str,
    top_k: int | None = 10,
) -> tuple[Action, SearchStats]:
    stats = SearchStats()
    actions = _ordered_actions(state, get_legal_actions(state), player, top_k)
    if not actions:
        raise ValueError("No legal actions")
    scored = [(action, _expected_after_action(state, action, depth - 1, player, stats, top_k)) for action in actions]
    return max(scored, key=lambda item: item[1])[0], stats


def _expectimax(state: GameState, depth: int, player: str, stats: SearchStats, top_k: int | None) -> float:
    stats.nodes += 1
    if depth <= 0 or state.is_terminal:
        return evaluate_state(state, player)
    actions = _ordered_actions(state, get_legal_actions(state), player, top_k)
    if not actions:
        return evaluate_state(state, player)
    values = [_expected_after_action(state, action, depth - 1, player, stats, top_k) for action in actions]
    return max(values) if state.current_player == player else min(values)


def _expected_after_action(
    state: GameState,
    action: Action,
    depth: int,
    player: str,
    stats: SearchStats,
    top_k: int | None,
) -> float:
    draws = possible_draws(state, action.card_type)
    if not draws:
        return _expectimax(apply_action(state, action), depth, player, stats, top_k)
    return sum(
        probability * _expectimax(apply_action(state, action, draw_card=card), depth, player, stats, top_k)
        for card, probability in draws.items()
    )


def _ordered_actions(state: GameState, actions: list[Action], player: str, top_k: int | None) -> list[Action]:
    maximizing = state.current_player == player
    ordered = sorted(
        actions,
        key=lambda action: evaluate_state(public_ordering_successor(state, action), player),
        reverse=maximizing,
    )
    return ordered[:top_k] if top_k else ordered
