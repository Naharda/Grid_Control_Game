from __future__ import annotations

from game.actions import Action
from game.state import GameState
from search.expectimax import choose_expectimax
from search.minimax import choose_minimax

from .base import Agent


class SearchAgent(Agent):
    def __init__(self, method: str = "expectimax", depth: int = 2, top_k: int | None = 10) -> None:
        self.method = method
        self.depth = depth
        self.top_k = top_k
        self.last_nodes = 0

    def choose_action(self, state: GameState, legal_actions: list[Action]) -> Action:
        if self.method == "minimax":
            action, stats = choose_minimax(state, self.depth, state.current_player, self.top_k)
        elif self.method == "expectimax":
            action, stats = choose_expectimax(state, self.depth, state.current_player, self.top_k)
        else:
            raise ValueError(f"Unknown search method: {self.method}")
        self.last_nodes = stats.nodes
        return action
