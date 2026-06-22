from __future__ import annotations

from game.actions import Action
from game.state import GameState
from visualization.text_view import render_state

from .base import Agent


class HumanAgent(Agent):
    def choose_action(self, state: GameState, legal_actions: list[Action]) -> Action:
        print(render_state(state))
        for idx, action in enumerate(legal_actions):
            print(f"{idx}: {action.compact()}")
        while True:
            raw = input("Choose action index: ").strip()
            if raw.isdigit() and 0 <= int(raw) < len(legal_actions):
                return legal_actions[int(raw)]
            print("Invalid action index.")
