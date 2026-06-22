from __future__ import annotations

from enum import Enum


class CardType(str, Enum):
    MOVE1 = "move1"
    MOVE2 = "move2"
    MOBILIZE = "mobilize"
    CAPTURE = "capture"
    SWAP = "swap"


CARD_LABELS = {
    CardType.MOVE1: "Move 1",
    CardType.MOVE2: "Move 2",
    CardType.MOBILIZE: "Mobilize",
    CardType.CAPTURE: "Capture",
    CardType.SWAP: "Swap",
}


def card_from_value(value: str | CardType) -> CardType:
    if isinstance(value, CardType):
        return value
    return CardType(value)
