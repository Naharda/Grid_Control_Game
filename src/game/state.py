from __future__ import annotations

import random
from dataclasses import dataclass, replace

from .board import Board, Position
from .cards import CardType
from .config import GameConfig


@dataclass(frozen=True)
class GameState:
    config: GameConfig
    board: Board
    current_player: str
    turn_counts: dict[str, int]
    positions: dict[str, tuple[Position, ...]]
    scores: dict[str, int]
    market: tuple[CardType, ...]
    deck: tuple[CardType, ...]
    discard: tuple[CardType, ...]
    rng_state: object
    consecutive_passes: int = 0
    last_action: str | None = None

    @property
    def opponent(self) -> str:
        return "B" if self.current_player == "A" else "A"

    @property
    def is_terminal(self) -> bool:
        score_goal = self.config.score_to_win
        return (
            score_goal is not None
            and any(score >= score_goal for score in self.scores.values())
        ) or all(v >= self.config.turns_per_player for v in self.turn_counts.values())

    @property
    def round_number(self) -> int:
        return min(self.turn_counts.values()) + 1

    def occupied(self) -> dict[Position, tuple[str, int]]:
        out: dict[Position, tuple[str, int]] = {}
        for player, pieces in self.positions.items():
            for idx, pos in enumerate(pieces):
                out[pos] = (player, idx)
        return out

    def as_hashable(self, include_deck: bool = True) -> tuple:
        base = (
            self.current_player,
            tuple(sorted(self.turn_counts.items())),
            tuple(sorted((p, tuple(v)) for p, v in self.positions.items())),
            tuple(sorted(self.scores.items())),
            self.market,
            self.consecutive_passes,
        )
        if include_deck:
            return base + (self.deck, self.discard)
        return base

    def with_updates(self, **kwargs) -> "GameState":
        return replace(self, **kwargs)


def build_deck(config: GameConfig, rng: random.Random) -> tuple[CardType, ...]:
    cards: list[CardType] = []
    for card, count in config.deck_composition.items():
        cards.extend([card] * count)
    rng.shuffle(cards)
    return tuple(cards)


def initial_state(config: GameConfig | None = None) -> GameState:
    config = config or GameConfig()
    rng = random.Random(config.seed)
    deck_list = list(build_deck(config, rng))
    market = tuple(deck_list[: config.market_size])
    deck = tuple(deck_list[config.market_size :])
    rows, cols = config.board_size
    return GameState(
        config=config,
        board=Board.grid(rows, cols, set(config.blocked_cells)),
        current_player="A",
        turn_counts={"A": 0, "B": 0},
        positions={"A": config.player_a_spawns, "B": config.player_b_spawns},
        scores={"A": 0, "B": 0},
        market=market,
        deck=deck,
        discard=(),
        rng_state=rng.getstate(),
        consecutive_passes=0,
    )
