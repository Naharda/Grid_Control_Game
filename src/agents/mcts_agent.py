from __future__ import annotations

from game.actions import Action
from game.state import GameState
from search.mcts import choose_mcts

from .base import Agent


class MCTSAgent(Agent):
    def __init__(self, simulations: int = 200, rollout_depth: int = 20, seed: int | None = None) -> None:
        self.simulations = simulations
        self.rollout_depth = rollout_depth
        self.seed = seed

    def choose_action(self, state: GameState, legal_actions: list[Action]) -> Action:
        return choose_mcts(state, state.current_player, self.simulations, self.rollout_depth, seed=self.seed)
