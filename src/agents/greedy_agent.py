from __future__ import annotations

from game.actions import Action
from game.state import GameState
from search.chance import public_ordering_successor
from search.heuristic import evaluate_state

from .base import Agent


class GreedyAgent(Agent):
    def choose_action(self, state: GameState, legal_actions: list[Action]) -> Action:
        player = state.current_player
        return max(
            legal_actions,
            key=lambda action: evaluate_state(public_ordering_successor(state, action), player),
        )
