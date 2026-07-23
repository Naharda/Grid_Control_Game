"""Reconstruct a recorded game from a mode's config and its games CSV.

Rebuilds the initial state from the mode config and the game's seed, then
replays every logged move (with forced card draws), validating each row's
snapshot along the way and cross-checking the final score against the pair's
results CSV. With --gui the full trajectory opens in the pygame viewer's
history review (Back/Next/arrow keys).

    python src/experiments/reconstruct_game.py <mode> <agent_a> <agent_b> <game_index> [--gui]
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.modes import config_from_mode, games_dir, load_mode, pair_key, results_path
from game.match_log import ReplayError, read_game_csv, replay_rows
from game.state import GameState, initial_state


def reconstruct_states(
    mode: dict,
    agent_a: str,
    agent_b: str,
    game_index: int,
    validate: bool = True,
    root: Path | None = None,
) -> list[GameState]:
    seeds = mode["game_seeds"]
    if not 0 <= game_index < len(seeds):
        raise SystemExit(f"game_index must be in 0..{len(seeds) - 1} for mode {mode['mode_name']!r}")
    game_path = games_dir(mode["mode_name"], agent_a, agent_b, root) / f"{game_index}.csv"
    if not game_path.exists():
        raise SystemExit(f"No recorded game at {game_path}")

    initial = initial_state(config_from_mode(mode, seed=seeds[game_index]))
    states = replay_rows(initial, read_game_csv(game_path), validate=validate)

    if validate:
        _check_against_results(mode, agent_a, agent_b, game_index, states[-1], root)
    return states


def _check_against_results(
    mode: dict, agent_a: str, agent_b: str, game_index: int, final: GameState, root: Path | None
) -> None:
    path = results_path(mode["mode_name"], agent_a, agent_b, root)
    if not path.exists():
        return
    with open(path, newline="", encoding="utf-8") as handle:
        rows = [row for row in csv.DictReader(handle) if int(row["game"]) == game_index]
    if not rows:
        return
    row = rows[0]
    scores = {"A": int(row["score_a"]), "B": int(row["score_b"])}
    if final.scores != scores:
        raise ReplayError(
            f"replayed final scores {final.scores} do not match results CSV {scores} ({path})"
        )
    winner = "A" if scores["A"] > scores["B"] else "B" if scores["B"] > scores["A"] else "draw"
    if row["winner"] != winner:
        raise ReplayError(f"results CSV winner {row['winner']!r} inconsistent with scores {scores}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Replay and validate a recorded mode game.")
    parser.add_argument("mode", help="Mode name under modes/.")
    parser.add_argument("agent_a")
    parser.add_argument("agent_b")
    parser.add_argument("game_index", type=int)
    parser.add_argument("--gui", action="store_true", help="Open the trajectory in the pygame viewer.")
    parser.add_argument("--no-validate", action="store_true", help="Skip per-row snapshot validation.")
    parser.add_argument("--modes-root", type=Path, help="Override the modes/ directory (mainly for tests).")
    args = parser.parse_args()

    mode = load_mode(args.mode, root=args.modes_root)
    try:
        states = reconstruct_states(
            mode, args.agent_a, args.agent_b, args.game_index,
            validate=not args.no_validate, root=args.modes_root,
        )
    except ReplayError as exc:
        raise SystemExit(f"Reconstruction failed: {exc}")

    final = states[-1]
    label = pair_key(args.agent_a, args.agent_b)
    checked = "validated" if not args.no_validate else "not validated"
    print(f"Reconstructed {label} game {args.game_index}: {len(states) - 1} turns, "
          f"final score A={final.scores['A']} B={final.scores['B']} ({checked}).")

    if args.gui:
        from visualization.pygame_view import run_pygame_game

        run_pygame_game(history=states)


if __name__ == "__main__":
    main()
