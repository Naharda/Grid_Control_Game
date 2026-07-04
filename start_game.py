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
from game.engine import play_match
from game.match_log import GameCsvRecorder, rows_from_history, write_game_csv
from game.state import initial_state
from visualization.pygame_view import run_pygame_game
from visualization.text_view import render_state


def resolve_agent(mode: dict | None, cli_name: str | None, position: int, fallback: str) -> tuple[str, dict | None]:
    if mode:
        return mode_agent_spec(mode, cli_name, position)
    return cli_name or fallback, None


def record_game(mode: dict, rows: list[dict], market_size: int, seed: int, source: str) -> None:
    if not rows:
        print("Nothing to record: no moves were played.")
        return
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = gui_record_path(mode["mode_name"], source, seed, timestamp)
    write_game_csv(path, rows, market_size)
    print(f"Recorded game to {path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Start a Graph Card Control match.")
    parser.add_argument("--a", choices=AGENT_NAMES, help="Player A agent (default: human, or the mode's first agent).")
    parser.add_argument("--b", choices=AGENT_NAMES, help="Player B agent (default: greedy, or the mode's second agent).")
    parser.add_argument("--mode", help="Game mode name in modes/; sets board, deck, rules, and default agents.")
    parser.add_argument("--board", help="Board name in boards/ (or path to a board JSON).")
    parser.add_argument("--deck", help="Deck name in decks/ (or path to a deck JSON).")
    parser.add_argument("--seed", type=int, help="Game seed (default: the mode's first game seed, else 1).")
    parser.add_argument("--record", action="store_true",
                        help="With --mode: save the played game to modes/<mode>/games/ in the games-CSV format.")
    parser.add_argument("--gui", action="store_true", help="Start the Pygame visual game/review tool.")
    parser.add_argument("--show-initial", action="store_true", help="Print the initial board before the match.")
    parser.add_argument("--log", action="store_true", help="Print the last match log entries at the end.")
    args = parser.parse_args()

    if args.record and not args.mode:
        parser.error("--record requires --mode")

    config, mode = entry_game_setup(args.mode, args.board, args.deck, args.seed)
    state = initial_state(config)
    name_a, params_a = resolve_agent(mode, args.a, 0, "human")
    name_b, params_b = resolve_agent(mode, args.b, 1, "greedy")

    if args.gui:
        agent_a = None if name_a == "human" else build_agent(name_a, params_a)
        agent_b = None if name_b == "human" else build_agent(name_b, params_b)
        game = run_pygame_game(agent_a=agent_a, agent_b=agent_b, state=state)
        if args.record:
            rows = rows_from_history(game.history, game.actions, config.market_size)
            record_game(mode, rows, config.market_size, config.seed, "gui")
        return

    if args.show_initial:
        print(render_state(state))
        print()

    recorder = GameCsvRecorder(config.market_size) if args.record else None
    result = play_match(
        build_agent(name_a, params_a),
        build_agent(name_b, params_b),
        state,
        log=args.log,
        on_step=recorder.record_step if recorder else None,
    )
    print()
    print(f"Winner: {result.winner or 'draw'}")
    print(f"Final score: A={result.scores['A']} B={result.scores['B']}")
    print(f"Turns played: A={result.turns['A']} B={result.turns['B']}")
    if args.log:
        print()
        print("Last actions:")
        print("\n".join(result.log[-10:]))
    if recorder:
        record_game(mode, recorder.finalize(), config.market_size, config.seed, "text")


if __name__ == "__main__":
    main()
