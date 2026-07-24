from __future__ import annotations

from dataclasses import dataclass, field
from time import perf_counter
from typing import Callable

from agents.base import Agent

from .actions import Action
from .rules import apply_action, apply_pass, get_legal_actions
from .state import GameState, initial_state

StepObserver = Callable[[GameState, "Action | None", GameState], None]


@dataclass
class MatchResult:
    winner: str | None
    scores: dict[str, int]
    turns: dict[str, int]
    log: list[str] = field(default_factory=list)
    decision_time_seconds: dict[str, float] = field(default_factory=dict)
    decisions: dict[str, int] = field(default_factory=dict)


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
    decision_time_seconds = {"A": 0.0, "B": 0.0}
    decisions = {"A": 0, "B": 0}

    while not state.is_terminal:
        legal = get_legal_actions(state)
        if not legal:
            new_state = apply_pass(state)
            if on_step:
                on_step(state, None, new_state)
            state = new_state
            continue
        player = state.current_player
        started = perf_counter()
        action = agents[player].choose_action(state, legal)
        decision_time_seconds[player] += perf_counter() - started
        decisions[player] += 1
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
    return MatchResult(
        winner=winner,
        scores=state.scores,
        turns=state.turn_counts,
        log=history,
        decision_time_seconds=decision_time_seconds,
        decisions=decisions,
    )
