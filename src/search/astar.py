from __future__ import annotations

import heapq
from dataclasses import dataclass

from game.actions import Action
from game.board import manhattan
from game.rules import apply_action, get_legal_actions
from game.state import GameState


@dataclass
class TacticalPlan:
    first_action: Action
    cost: float
    expanded: int
    reached_goal: bool


def astar_to_center(state: GameState, player: str, horizon: int = 6, expansion_limit: int = 500) -> TacticalPlan:
    legal = get_legal_actions(state)
    if not legal:
        raise ValueError("No legal actions")
    counter = 0
    frontier: list[tuple[float, int, int, GameState, Action]] = []
    for action in legal:
        nxt = apply_action(state, action)
        h = _center_distance(nxt, player)
        heapq.heappush(frontier, (1 + h, counter, 1, nxt, action))
        counter += 1

    best = frontier[0]
    expanded = 0
    seen: set[tuple] = set()
    while frontier and expanded < expansion_limit:
        item = heapq.heappop(frontier)
        _, _, cost, cur, first_action = item
        key = cur.as_hashable(include_deck=False)
        if key in seen:
            continue
        seen.add(key)
        best = item
        expanded += 1
        if cur.config.center in cur.positions[player]:
            return TacticalPlan(first_action, cost, expanded, True)
        if cost >= horizon:
            continue
        for action in get_legal_actions(cur):
            nxt = apply_action(cur, action)
            heapq.heappush(frontier, (cost + 1 + _center_distance(nxt, player), counter, cost + 1, nxt, first_action))
            counter += 1
    return TacticalPlan(best[4], best[2], expanded, False)


def _center_distance(state: GameState, player: str) -> int:
    return min(manhattan(pos, state.config.center) for pos in state.positions[player])
