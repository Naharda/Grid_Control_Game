from __future__ import annotations

from dataclasses import dataclass

from .board import Position
from .cards import CardType


@dataclass(frozen=True)
class PieceMove:
    piece_id: int
    to_pos: Position


@dataclass(frozen=True)
class Action:
    card_index: int
    card_type: CardType
    moves: tuple[PieceMove, ...] = ()
    target_piece: tuple[str, int] | None = None
    swap_piece: tuple[str, int] | None = None
    mode: str = "base"

    def compact(self) -> str:
        bits = [f"{self.card_index}:{self.card_type.value}"]
        if self.moves:
            bits.append("moves=" + ",".join(f"{m.piece_id}->{m.to_pos}" for m in self.moves))
        if self.target_piece:
            bits.append(f"target={self.target_piece[0]}{self.target_piece[1]}")
        if self.swap_piece:
            bits.append(f"swap={self.swap_piece[0]}{self.swap_piece[1]}")
        if self.mode != "base":
            bits.append(self.mode)
        return " ".join(bits)
