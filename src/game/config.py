from __future__ import annotations

from dataclasses import dataclass, field

from .cards import CardType


@dataclass(frozen=True)
class GameConfig:
    board_size: tuple[int, int] = (5, 5)
    pieces_per_player: int = 3
    turns_per_player: int = 50
    market_size: int = 3
    center_score: int = 1
    capture_score: int = 3
    swap_range: int = 3
    net_range: int = 3
    market_refresh_after_passes: int | None = None
    score_to_win: int | None = None
    seed: int | None = 1
    player_a_spawns: tuple[tuple[int, int], ...] = ((0, 1), (0, 2), (0, 3))
    player_b_spawns: tuple[tuple[int, int], ...] = ((4, 1), (4, 2), (4, 3))
    capture_cells: dict[tuple[int, int], int] | None = None
    blocked_cells: tuple[tuple[int, int], ...] = ()
    deck_composition: dict[CardType, int] = field(
        default_factory=lambda: {
            CardType.MOVE1: 8,
            CardType.MOVE2: 6,
            CardType.MOBILIZE: 5,
            CardType.CAPTURE: 5,
            CardType.SWAP: 4,
        }
    )
    heuristic_weights: dict[str, float] = field(
        default_factory=lambda: {
            "score": 100,
            "center": 10,
            "center_distance": 2,
            "capture_threat": 15,
            "net_potential": 20,
            "swap_potential": 8,
            "safety": 10,
            "mobility": 1,
        }
    )

    @property
    def center(self) -> tuple[int, int]:
        """Geometric middle of the board; scoring uses `scoring_cells`."""
        rows, cols = self.board_size
        return rows // 2, cols // 2

    @property
    def scoring_cells(self) -> dict[tuple[int, int], int]:
        if self.capture_cells is not None:
            return dict(self.capture_cells)
        return {self.center: self.center_score}

    def spawns_for(self, player: str) -> tuple[tuple[int, int], ...]:
        return self.player_a_spawns if player == "A" else self.player_b_spawns
