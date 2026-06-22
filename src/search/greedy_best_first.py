from __future__ import annotations

import heapq
from dataclasses import dataclass

from game.actions import Action
from game.rules import apply_action, get_legal_actions
from game.state import GameState
from search.heuristic import evaluate_state


@dataclass
class PlanResult:
    first_action: Action
    best_value: float
    expanded: int


def greedy_best_first_plan(
    state: GameState,
    player: str,
    horizon: int = 4,
    expansion_limit: int = 200,
) -> PlanResult:
    legal = get_legal_actions(state)
    if not legal:
        raise ValueError("No legal actions")
    counter = 0
    frontier: list[tuple[float, int, int, GameState, Action]] = []
    for action in legal:
        nxt = apply_action(state, action)
        heapq.heappush(frontier, (-evaluate_state(nxt, player), counter, 1, nxt, action))
        counter += 1

    best = frontier[0]
    expanded = 0
    while frontier and expanded < expansion_limit:
        item = heapq.heappop(frontier)
        score, _, depth, cur, first_action = item
        if score < best[0]:
            best = item
        expanded += 1
        if depth >= horizon or cur.is_terminal:
            continue
        for action in get_legal_actions(cur):
            nxt = apply_action(cur, action)
            heapq.heappush(frontier, (-evaluate_state(nxt, player), counter, depth + 1, nxt, first_action))
            counter += 1
    return PlanResult(first_action=best[4], best_value=-best[0], expanded=expanded)
