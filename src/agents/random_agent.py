from __future__ import annotations

import random

from game.actions import Action
from game.state import GameState

from .base import Agent


class RandomAgent(Agent):
    def __init__(self, seed: int | None = None) -> None:
        self.rng = random.Random(seed)

    def choose_action(self, state: GameState, legal_actions: list[Action]) -> Action:
        return self.rng.choice(legal_actions)
