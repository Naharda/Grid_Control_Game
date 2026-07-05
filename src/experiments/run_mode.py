"""Run every game of a game mode and record results plus per-game move logs.

For each ordered pair of the mode's agents (both A-vs-B and B-vs-A; a mirror
pair runs once) and each game seed, this plays one match and writes:

    modes/<mode>/results/<agent1>_<agent2>.csv   # game,agent_a,agent_b,winner,score_a,score_b
    modes/<mode>/games/<agent1>_<agent2>/<i>.csv # per-turn move log (game.match_log format)

Both orders of a pair reuse the same seeds, so game i starts from the same
shuffled deck in either orientation.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from time import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.modes import (
    config_from_mode,
    effective_agent_params,
    games_dir,
    load_mode,
    ordered_pairs,
    pair_key,
    results_path,
)
from experiments.run_match import build_agent
from game.engine import play_match
from game.match_log import GameCsvRecorder, write_game_csv
from game.state import initial_state

RESULTS_FIELDS = ["game", "agent_a", "agent_b", "winner", "score_a", "score_b"]

def _get_elapsed(start_time: float, as_string: bool = True) -> float:
    """Get the elapsed time since start_time, optionally formatted as a string.
    String format: [D:]HH:MM:SS
    """
    _elapsed = time() - start_time
    if as_string:
        hours, rem = divmod(_elapsed, 3600)
        minutes, seconds = divmod(rem, 60)
        days, hours = divmod(hours, 24)
        if days > 0:
            return f"{int(days)}:{int(hours):02}:{int(minutes):02}:{int(seconds):02}"
        else:
            return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"
    return _elapsed

def run_pair(mode: dict, name_a: str, name_b: str, root: Path | None = None) -> dict[str, int]:
    agents = {entry["name"]: entry["params"] for entry in mode["agents"]}
    policy = mode.get("agent_seed_policy", "derived")
    mode_name = mode["mode_name"]
    pair_games_dir = games_dir(mode_name, name_a, name_b, root)

    rows = []
    wins = {"A": 0, "B": 0, "draw": 0}
    for game_index, seed in enumerate(mode["game_seeds"]):
        config = config_from_mode(mode, seed=seed)
        agent_a = build_agent(name_a, effective_agent_params(agents[name_a], policy, seed, 0))
        agent_b = build_agent(name_b, effective_agent_params(agents[name_b], policy, seed, 1))
        recorder = GameCsvRecorder(config.market_size)
        result = play_match(agent_a, agent_b, initial_state(config), on_step=recorder.record_step)
        write_game_csv(pair_games_dir / f"{game_index}.csv", recorder.finalize(), config.market_size)
        wins[result.winner or "draw"] += 1
        rows.append(
            {
                "game": game_index,
                "agent_a": name_a,
                "agent_b": name_b,
                "winner": result.winner or "draw",
                "score_a": result.scores["A"],
                "score_b": result.scores["B"],
            }
        )

    out_path = results_path(mode_name, name_a, name_b, root)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=RESULTS_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return wins


def run_mode(mode: dict, pairs: list[tuple[str, str]] | None = None, force: bool = False,
             root: Path | None = None) -> None:
    agent_names = [entry["name"] for entry in mode["agents"]]
    pairs = pairs if pairs is not None else ordered_pairs(agent_names)
    print(f"Running {len(pairs)} pairs of {len(mode['game_seeds'])} games each for mode '{mode['mode_name']}'")
    s_run = time()
    for a, b in pairs:
        existing = results_path(mode["mode_name"], a, b, root)
        if existing.exists() and not force:
            raise SystemExit(f"{existing} already exists; re-run with --force to overwrite")

    for i, (a, b) in enumerate(pairs):
        s_pair = time()
        print(f"Running {pair_key(a, b)}... ({i + 1}/{len(pairs)} | Elapsed: {_get_elapsed(s_run, as_string=True)})")
        wins = run_pair(mode, a, b, root)
        t_pair = time() - s_pair
        t_round = t_pair/(len(mode['game_seeds']) or 1)
        elapsed_pair = _get_elapsed(t_pair, as_string=True)
        elapsed_round = _get_elapsed(t_round, as_string=True)
        print(f"{pair_key(a, b)}: {len(mode['game_seeds'])} games, "
              f"A({a}) wins={wins['A']} B({b}) wins={wins['B']} draws={wins['draw']} "
              f"[{elapsed_pair} ({elapsed_round} * {len(mode['game_seeds'])})]")


def parse_pair(text: str, agent_names: list[str]) -> tuple[str, str]:
    for a in agent_names:
        prefix = f"{a}_"
        if text.startswith(prefix) and text[len(prefix):] in agent_names:
            return a, text[len(prefix):]
    raise SystemExit(f"Unknown pair {text!r}; mode agents are {agent_names}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run all games of a game mode.")
    parser.add_argument("name", help="Mode name under modes/.")
    parser.add_argument("--pairs", nargs="+", metavar="A_B",
                        help="Only run these ordered pairs (e.g. greedy_random). Default: all.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing results.")
    parser.add_argument("--modes-root", type=Path, help="Override the modes/ directory (mainly for tests).")
    args = parser.parse_args()

    mode = load_mode(args.name, root=args.modes_root)
    agent_names = [entry["name"] for entry in mode["agents"]]
    pairs = [parse_pair(p, agent_names) for p in args.pairs] if args.pairs else None
    run_mode(mode, pairs=pairs, force=args.force, root=args.modes_root)


if __name__ == "__main__":
    main()
