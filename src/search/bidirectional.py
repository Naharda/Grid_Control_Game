from __future__ import annotations

from collections import deque
from dataclasses import dataclass

from game.board import Position, manhattan
from game.state import GameState


@dataclass(frozen=True)
class PatternSearchResult:
    found: bool
    distance: int | None
    expanded: int


def bidirectional_piece_to_center(state: GameState, player: str, max_depth: int = 6) -> PatternSearchResult:
    starts = frozenset(state.positions[player])
    goals = frozenset({state.config.center})
    if state.config.center in starts:
        return PatternSearchResult(True, 0, 0)

    forward = deque([(pos, 0) for pos in starts])
    backward = deque([(state.config.center, 0)])
    f_seen = {pos: 0 for pos in starts}
    b_seen = {state.config.center: 0}
    occupied = set(state.occupied()) - starts
    expanded = 0

    while forward and backward and expanded < 500:
        meet = _expand_frontier(state, forward, f_seen, b_seen, occupied, max_depth)
        expanded += 1
        if meet is not None:
            return PatternSearchResult(True, meet, expanded)
        meet = _expand_frontier(state, backward, b_seen, f_seen, occupied, max_depth)
        expanded += 1
        if meet is not None:
            return PatternSearchResult(True, meet, expanded)
    return PatternSearchResult(False, None, expanded)


def _expand_frontier(
    state: GameState,
    queue: deque[tuple[Position, int]],
    mine: dict[Position, int],
    theirs: dict[Position, int],
    occupied: set[Position],
    max_depth: int,
) -> int | None:
    if not queue:
        return None
    pos, dist = queue.popleft()
    if dist >= max_depth:
        return None
    for nxt in state.board.neighbors(pos):
        if nxt in occupied or nxt in mine:
            continue
        mine[nxt] = dist + 1
        if nxt in theirs:
            return mine[nxt] + theirs[nxt]
        queue.append((nxt, dist + 1))
    return None


def aligned_net_pattern_score(state: GameState, player: str) -> int:
    pieces = state.positions[player]
    score = 0
    for i, a in enumerate(pieces):
        for b in pieces[i + 1 :]:
            if manhattan(a, b) == 1:
                score += 3
            else:
                score += max(0, 2 - min(abs(a[0] - b[0]), abs(a[1] - b[1])))
    enemy = "B" if player == "A" else "A"
    for a in pieces:
        for e in state.positions[enemy]:
            if manhattan(a, e) <= state.config.net_range:
                score += 1
    return score
