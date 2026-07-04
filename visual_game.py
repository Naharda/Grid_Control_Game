from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

SRC = Path(__file__).resolve().parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from experiments.modes import entry_game_setup, gui_record_path, mode_agent_spec
from experiments.run_match import AGENT_NAMES, build_agent
from game.match_log import rows_from_history, write_game_csv
from game.state import initial_state
from visualization.pygame_view import run_pygame_game


def main() -> None:
    parser = argparse.ArgumentParser(description="Launch the Pygame Graph Card Control tool.")
    parser.add_argument("--a", choices=AGENT_NAMES, help="Player A agent (default: human, or the mode's first agent).")
    parser.add_argument("--b", choices=AGENT_NAMES, help="Player B agent (default: greedy, or the mode's second agent).")
    parser.add_argument("--mode", help="Game mode name in modes/; sets board, deck, rules, and default agents.")
    parser.add_argument("--board", help="Board name in boards/ (or path to a board JSON).")
    parser.add_argument("--deck", help="Deck name in decks/ (or path to a deck JSON).")
    parser.add_argument("--seed", type=int, help="Game seed (default: the mode's first game seed, else 1).")
    parser.add_argument("--record", action="store_true",
                        help="With --mode: save the played game to modes/<mode>/games/ in the games-CSV format.")
    args = parser.parse_args()

    if args.record and not args.mode:
        parser.error("--record requires --mode")

    config, mode = entry_game_setup(args.mode, args.board, args.deck, args.seed)
    if mode:
        name_a, params_a = mode_agent_spec(mode, args.a, 0)
        name_b, params_b = mode_agent_spec(mode, args.b, 1)
    else:
        name_a, params_a = args.a or "human", None
        name_b, params_b = args.b or "greedy", None

    agent_a = None if name_a == "human" else build_agent(name_a, params_a)
    agent_b = None if name_b == "human" else build_agent(name_b, params_b)
    game = run_pygame_game(agent_a=agent_a, agent_b=agent_b, state=initial_state(config))

    if args.record:
        rows = rows_from_history(game.history, game.actions, config.market_size)
        if not rows:
            print("Nothing to record: no moves were played.")
            return
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        path = gui_record_path(mode["mode_name"], "gui", config.seed, timestamp)
        write_game_csv(path, rows, config.market_size)
        print(f"Recorded game to {path}")


if __name__ == "__main__":
    main()
