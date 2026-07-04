from __future__ import annotations

import argparse
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from experiments.run_match import AGENT_NAMES, build_agent
from game.engine import play_match
from game.setup_loader import build_config, load_board, load_deck
from game.state import initial_state
from visualization.pygame_view import run_pygame_game
from visualization.text_view import render_state


def main() -> None:
    parser = argparse.ArgumentParser(description="Start a Graph Card Control match.")
    parser.add_argument("--a", default="human", choices=AGENT_NAMES, help="Player A agent.")
    parser.add_argument("--b", default="greedy", choices=AGENT_NAMES, help="Player B agent.")
    parser.add_argument("--board", help="Board name in boards/ (or path to a board JSON).")
    parser.add_argument("--deck", help="Deck name in decks/ (or path to a deck JSON).")
    parser.add_argument("--seed", type=int, default=1, help="Game seed (deck shuffle).")
    parser.add_argument("--gui", action="store_true", help="Start the Pygame visual game/review tool.")
    parser.add_argument("--show-initial", action="store_true", help="Print the initial board before the match.")
    parser.add_argument("--log", action="store_true", help="Print the last match log entries at the end.")
    args = parser.parse_args()

    config = build_config(
        board=load_board(args.board) if args.board else None,
        deck=load_deck(args.deck) if args.deck else None,
        seed=args.seed,
    )
    state = initial_state(config)
    if args.gui:
        agent_a = None if args.a == "human" else build_agent(args.a)
        agent_b = None if args.b == "human" else build_agent(args.b)
        run_pygame_game(agent_a=agent_a, agent_b=agent_b, state=state)
        return

    if args.show_initial:
        print(render_state(state))
        print()

    result = play_match(build_agent(args.a), build_agent(args.b), state, log=args.log)
    print()
    print(f"Winner: {result.winner or 'draw'}")
    print(f"Final score: A={result.scores['A']} B={result.scores['B']}")
    print(f"Turns played: A={result.turns['A']} B={result.turns['B']}")
    if args.log:
        print()
        print("Last actions:")
        print("\n".join(result.log[-10:]))


if __name__ == "__main__":
    main()
