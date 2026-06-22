from __future__ import annotations

from game.actions import Action
from game.board import manhattan
from game.cards import CardType
from game.rules import apply_action
from game.state import GameState
from search.heuristic import evaluate_state

from .base import Agent


class RuleBasedAgent(Agent):
    """A transparent baseline: capture first, then fight for the center."""

    def choose_action(self, state: GameState, legal_actions: list[Action]) -> Action:
        player = state.current_player
        captures = [a for a in legal_actions if a.card_type == CardType.CAPTURE]
        if captures:
            return max(captures, key=lambda action: evaluate_state(apply_action(state, action), player))

        center_actions = [
            action
            for action in legal_actions
            if state.config.center in apply_action(state, action).positions[player]
        ]
        if center_actions:
            return max(center_actions, key=lambda action: evaluate_state(apply_action(state, action), player))

        movable = [
            action
            for action in legal_actions
            if action.card_type in {CardType.MOVE1, CardType.MOVE2, CardType.MOBILIZE, CardType.SWAP}
        ]
        if movable:
            return min(
                movable,
                key=lambda action: min(
                    manhattan(pos, state.config.center)
                    for pos in apply_action(state, action).positions[player]
                ),
            )

        return max(legal_actions, key=lambda action: evaluate_state(apply_action(state, action), player))
