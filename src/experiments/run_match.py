from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agents.greedy_agent import GreedyAgent
from agents.human_agent import HumanAgent
from agents.mcts_agent import MCTSAgent
from agents.random_agent import RandomAgent
from agents.rule_based_agent import RuleBasedAgent
from agents.search_agent import SearchAgent
from game.engine import play_match
from game.state import initial_state
from visualization.text_view import render_state


def build_agent(name: str):
    if name == "random":
        return RandomAgent()
    if name == "greedy":
        return GreedyAgent()
    if name == "rule":
        return RuleBasedAgent()
    if name == "human":
        return HumanAgent()
    if name == "minimax":
        return SearchAgent(method="minimax", depth=2, top_k=10)
    if name == "expectimax":
        return SearchAgent(method="expectimax", depth=2, top_k=10)
    if name == "mcts":
        return MCTSAgent(simulations=200, rollout_depth=20)
    raise ValueError(f"Unknown agent: {name}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--a", default="greedy", choices=["random", "rule", "greedy", "human", "minimax", "expectimax", "mcts"])
    parser.add_argument("--b", default="random", choices=["random", "rule", "greedy", "human", "minimax", "expectimax", "mcts"])
    parser.add_argument("--show-initial", action="store_true")
    parser.add_argument("--log", action="store_true")
    args = parser.parse_args()

    state = initial_state()
    if args.show_initial:
        print(render_state(state))
        print()
    result = play_match(build_agent(args.a), build_agent(args.b), state, log=args.log)
    print(f"Winner: {result.winner or 'draw'}")
    print(f"Scores: A={result.scores['A']} B={result.scores['B']}")
    print(f"Turns: A={result.turns['A']} B={result.turns['B']}")
    if args.log:
        print("\n".join(result.log[-10:]))


if __name__ == "__main__":
    main()
