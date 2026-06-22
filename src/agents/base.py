from __future__ import annotations

from abc import ABC, abstractmethod

from game.actions import Action
from game.state import GameState


class Agent(ABC):
    @abstractmethod
    def choose_action(self, state: GameState, legal_actions: list[Action]) -> Action:
        raise NotImplementedError
