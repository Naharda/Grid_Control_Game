from __future__ import annotations

from game.actions import Action
from game.cards import CardType
from game.state import GameState
from search.chance import public_ordering_successor
from search.heuristic import evaluate_state, nearest_scoring_distance

from .base import Agent


class RuleBasedAgent(Agent):
    """A transparent baseline: capture first, then fight for the center."""

    def choose_action(self, state: GameState, legal_actions: list[Action]) -> Action:
        player = state.current_player
        captures = [a for a in legal_actions if a.card_type == CardType.CAPTURE]
        if captures:
            return max(captures, key=lambda action: evaluate_state(public_ordering_successor(state, action), player))

        scoring = state.config.scoring_cells
        center_actions = [
            action
            for action in legal_actions
            if any(cell in public_ordering_successor(state, action).positions[player] for cell in scoring)
        ]
        if center_actions:
            return max(center_actions, key=lambda action: evaluate_state(public_ordering_successor(state, action), player))

        movable = [
            action
            for action in legal_actions
            if action.card_type in {CardType.MOVE1, CardType.MOVE2, CardType.MOBILIZE, CardType.SWAP}
        ]
        if movable:
            return min(
                movable,
                key=lambda action: min(
                    nearest_scoring_distance(pos, scoring)
                    for pos in public_ordering_successor(state, action).positions[player]
                ),
            )

        return max(
            legal_actions,
            key=lambda action: evaluate_state(public_ordering_successor(state, action), player),
        )
