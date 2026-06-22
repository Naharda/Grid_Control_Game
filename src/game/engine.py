from __future__ import annotations

from dataclasses import dataclass, field

from agents.base import Agent

from .rules import apply_action, get_legal_actions
from .state import GameState, initial_state


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
) -> MatchResult:
    state = state or initial_state()
    agents = {"A": agent_a, "B": agent_b}
    history: list[str] = []

    while not state.is_terminal:
        legal = get_legal_actions(state)
        if not legal:
            state = state.with_updates(
                current_player="B" if state.current_player == "A" else "A",
                turn_counts={**state.turn_counts, state.current_player: state.turn_counts[state.current_player] + 1},
                last_action="pass",
            )
            continue
        action = agents[state.current_player].choose_action(state, legal)
        state = apply_action(state, action)
        if log:
            history.append(f"{state.current_player} next after {state.last_action}; scores={state.scores}")

    if state.scores["A"] > state.scores["B"]:
        winner = "A"
    elif state.scores["B"] > state.scores["A"]:
        winner = "B"
    else:
        winner = None
    return MatchResult(winner=winner, scores=state.scores, turns=state.turn_counts, log=history)
