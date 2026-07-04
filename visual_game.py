from __future__ import annotations

import argparse
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from experiments.run_match import AGENT_NAMES, build_agent
from game.setup_loader import build_config, load_board, load_deck
from game.state import initial_state
from visualization.pygame_view import run_pygame_game


def main() -> None:
    parser = argparse.ArgumentParser(description="Launch the Pygame Graph Card Control tool.")
    parser.add_argument("--a", default="human", choices=AGENT_NAMES, help="Player A agent.")
    parser.add_argument("--b", default="greedy", choices=AGENT_NAMES, help="Player B agent.")
    parser.add_argument("--board", help="Board name in boards/ (or path to a board JSON).")
    parser.add_argument("--deck", help="Deck name in decks/ (or path to a deck JSON).")
    parser.add_argument("--seed", type=int, default=1, help="Game seed (deck shuffle).")
    args = parser.parse_args()

    config = build_config(
        board=load_board(args.board) if args.board else None,
        deck=load_deck(args.deck) if args.deck else None,
        seed=args.seed,
    )
    agent_a = None if args.a == "human" else build_agent(args.a)
    agent_b = None if args.b == "human" else build_agent(args.b)
    run_pygame_game(agent_a=agent_a, agent_b=agent_b, state=initial_state(config))


if __name__ == "__main__":
    main()
