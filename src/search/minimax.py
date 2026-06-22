from __future__ import annotations

from dataclasses import dataclass

from game.actions import Action
from game.rules import apply_action, get_legal_actions
from game.state import GameState
from search.heuristic import evaluate_state


@dataclass
class SearchStats:
    nodes: int = 0


def choose_minimax(
    state: GameState,
    depth: int,
    player: str,
    top_k: int | None = None,
) -> tuple[Action, SearchStats]:
    stats = SearchStats()
    actions = _ordered_actions(state, get_legal_actions(state), player, top_k)
    if not actions:
        raise ValueError("No legal actions")
    maximizing = state.current_player == player
    chooser = max if maximizing else min
    scored = [(action, _minimax(apply_action(state, action), depth - 1, player, -float("inf"), float("inf"), stats, top_k)) for action in actions]
    return chooser(scored, key=lambda item: item[1])[0], stats


def _minimax(
    state: GameState,
    depth: int,
    player: str,
    alpha: float,
    beta: float,
    stats: SearchStats,
    top_k: int | None,
) -> float:
    stats.nodes += 1
    if depth <= 0 or state.is_terminal:
        return evaluate_state(state, player)
    actions = _ordered_actions(state, get_legal_actions(state), player, top_k)
    if not actions:
        return evaluate_state(state, player)
    if state.current_player == player:
        value = -float("inf")
        for action in actions:
            value = max(value, _minimax(apply_action(state, action), depth - 1, player, alpha, beta, stats, top_k))
            alpha = max(alpha, value)
            if beta <= alpha:
                break
        return value
    value = float("inf")
    for action in actions:
        value = min(value, _minimax(apply_action(state, action), depth - 1, player, alpha, beta, stats, top_k))
        beta = min(beta, value)
        if beta <= alpha:
            break
    return value


def _ordered_actions(state: GameState, actions: list[Action], player: str, top_k: int | None) -> list[Action]:
    ordered = sorted(actions, key=lambda a: evaluate_state(apply_action(state, a), player), reverse=True)
    return ordered[:top_k] if top_k else ordered
