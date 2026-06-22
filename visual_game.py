from __future__ import annotations

import argparse
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from experiments.run_match import build_agent
from game.state import initial_state
from visualization.pygame_view import run_pygame_game


AGENTS = ["human", "random", "rule", "greedy", "minimax", "expectimax", "mcts"]


def main() -> None:
    parser = argparse.ArgumentParser(description="Launch the Pygame Graph Card Control tool.")
    parser.add_argument("--a", default="human", choices=AGENTS, help="Player A agent.")
    parser.add_argument("--b", default="greedy", choices=AGENTS, help="Player B agent.")
    args = parser.parse_args()

    agent_a = None if args.a == "human" else build_agent(args.a)
    agent_b = None if args.b == "human" else build_agent(args.b)
    run_pygame_game(agent_a=agent_a, agent_b=agent_b, state=initial_state())


if __name__ == "__main__":
    main()
