from __future__ import annotations

from collections import deque
from dataclasses import dataclass

Position = tuple[int, int]


@dataclass(frozen=True)
class Board:
    rows: int
    cols: int
    blocked: frozenset[Position] = frozenset()

    @classmethod
    def grid(cls, rows: int, cols: int, blocked: set[Position] | None = None) -> "Board":
        return cls(rows=rows, cols=cols, blocked=frozenset(blocked or set()))

    @property
    def positions(self) -> tuple[Position, ...]:
        return tuple(
            (r, c)
            for r in range(self.rows)
            for c in range(self.cols)
            if (r, c) not in self.blocked
        )

    def in_bounds(self, pos: Position) -> bool:
        r, c = pos
        return 0 <= r < self.rows and 0 <= c < self.cols and pos not in self.blocked

    def neighbors(self, pos: Position) -> tuple[Position, ...]:
        r, c = pos
        candidates = ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1))
        return tuple(p for p in candidates if self.in_bounds(p))

    def shortest_distance(self, start: Position, goal: Position) -> int:
        if start == goal:
            return 0
        queue: deque[tuple[Position, int]] = deque([(start, 0)])
        seen = {start}
        while queue:
            pos, dist = queue.popleft()
            for nxt in self.neighbors(pos):
                if nxt in seen:
                    continue
                if nxt == goal:
                    return dist + 1
                seen.add(nxt)
                queue.append((nxt, dist + 1))
        return 10**6

    def reachable(self, start: Position, max_steps: int, occupied: set[Position]) -> tuple[Position, ...]:
        queue: deque[tuple[Position, int]] = deque([(start, 0)])
        seen = {start}
        out: list[Position] = []
        while queue:
            pos, dist = queue.popleft()
            if dist == max_steps:
                continue
            for nxt in self.neighbors(pos):
                if nxt in seen or nxt in occupied:
                    continue
                seen.add(nxt)
                out.append(nxt)
                queue.append((nxt, dist + 1))
        return tuple(out)

    def ray(self, start: Position, direction: Position, max_steps: int) -> tuple[Position, ...]:
        dr, dc = direction
        r, c = start
        cells: list[Position] = []
        for _ in range(max_steps):
            r += dr
            c += dc
            pos = (r, c)
            if not self.in_bounds(pos):
                break
            cells.append(pos)
        return tuple(cells)


ORTHOGONAL_DIRECTIONS: tuple[Position, ...] = ((-1, 0), (1, 0), (0, -1), (0, 1))


def manhattan(a: Position, b: Position) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])
