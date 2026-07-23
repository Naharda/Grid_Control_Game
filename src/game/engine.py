from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from agents.base import Agent

from .actions import Action
from .rules import apply_action, get_legal_actions
from .state import GameState, initial_state

StepObserver = Callable[[GameState, "Action | None", GameState], None]


@dataclass
class MatchResult:
    winner: str | None
    scores: dict[str, int]
    turns: dict[str, int]
    log: list[str] = field(default_factory=list)


def play_match(
    agent_a: Agent,
    agent_b: Agent,
    state: GameState | None = None,
    log: bool = False,
    on_step: StepObserver | None = None,
) -> MatchResult:
    state = state or initial_state()
    agents = {"A": agent_a, "B": agent_b}
    history: list[str] = []

    while not state.is_terminal:
        legal = get_legal_actions(state)
        if not legal:
            new_state = state.with_updates(
                current_player="B" if state.current_player == "A" else "A",
                turn_counts={**state.turn_counts, state.current_player: state.turn_counts[state.current_player] + 1},
                last_action="pass",
            )
            if on_step:
                on_step(state, None, new_state)
            state = new_state
            continue
        action = agents[state.current_player].choose_action(state, legal)
        new_state = apply_action(state, action)
        if on_step:
            on_step(state, action, new_state)
        state = new_state
        if log:
            history.append(f"{state.current_player} next after {state.last_action}; scores={state.scores}")

    if state.scores["A"] > state.scores["B"]:
        winner = "A"
    elif state.scores["B"] > state.scores["A"]:
        winner = "B"
    else:
        winner = None
    return MatchResult(winner=winner, scores=state.scores, turns=state.turn_counts, log=history)
