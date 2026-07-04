from __future__ import annotations

import argparse
import copy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agents.base import Agent
from agents.greedy_agent import GreedyAgent
from agents.human_agent import HumanAgent
from agents.mcts_agent import MCTSAgent
from agents.random_agent import RandomAgent
from agents.rule_based_agent import RuleBasedAgent
from agents.search_agent import SearchAgent
from experiments.modes import entry_game_setup, mode_agent_spec
from game.engine import play_match
from game.state import initial_state
from visualization.text_view import render_state

AGENT_SPECS: dict[str, tuple[type, dict]] = {
    "random": (RandomAgent, {"seed": None}),
    "greedy": (GreedyAgent, {}),
    "rule": (RuleBasedAgent, {}),
    "human": (HumanAgent, {}),
    "minimax": (SearchAgent, {"method": "minimax", "depth": 2, "top_k": 10}),
    "expectimax": (SearchAgent, {"method": "expectimax", "depth": 2, "top_k": 10}),
    "mcts": (MCTSAgent, {"simulations": 200, "rollout_depth": 20, "seed": None}),
}
AGENT_NAMES = list(AGENT_SPECS)


def default_params(name: str) -> dict:
    if name not in AGENT_SPECS:
        raise ValueError(f"Unknown agent: {name}")
    return copy.deepcopy(AGENT_SPECS[name][1])


def build_agent(name: str, params: dict | None = None) -> Agent:
    if name not in AGENT_SPECS:
        raise ValueError(f"Unknown agent: {name}")
    cls, defaults = AGENT_SPECS[name]
    merged = {**defaults, **(params or {})}
    unknown = set(merged) - set(defaults)
    if unknown:
        raise ValueError(f"Unknown params for agent {name!r}: {sorted(unknown)}")
    return cls(**merged)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--a", choices=AGENT_NAMES, help="Player A agent (default: greedy, or the mode's first agent).")
    parser.add_argument("--b", choices=AGENT_NAMES, help="Player B agent (default: random, or the mode's second agent).")
    parser.add_argument("--mode", help="game mode name in modes/; sets board, deck, rules, and default agents")
    parser.add_argument("--board", help="board name in boards/ (or path to a board JSON)")
    parser.add_argument("--deck", help="deck name in decks/ (or path to a deck JSON)")
    parser.add_argument("--seed", type=int, help="game seed (default: the mode's first game seed, else 1)")
    parser.add_argument("--show-initial", action="store_true")
    parser.add_argument("--log", action="store_true")
    args = parser.parse_args()

    config, mode = entry_game_setup(args.mode, args.board, args.deck, args.seed)
    if mode:
        name_a, params_a = mode_agent_spec(mode, args.a, 0)
        name_b, params_b = mode_agent_spec(mode, args.b, 1)
    else:
        name_a, params_a = args.a or "greedy", None
        name_b, params_b = args.b or "random", None

    state = initial_state(config)
    if args.show_initial:
        print(render_state(state))
        print()
    result = play_match(build_agent(name_a, params_a), build_agent(name_b, params_b), state, log=args.log)
    print(f"Winner: {result.winner or 'draw'}")
    print(f"Scores: A={result.scores['A']} B={result.scores['B']}")
    print(f"Turns: A={result.turns['A']} B={result.turns['B']}")
    if args.log:
        print("\n".join(result.log[-10:]))


if __name__ == "__main__":
    main()
