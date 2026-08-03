"""Run and replay-validate the corrected experiment suite, resumably."""

from __future__ import annotations

import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from experiments.modes import games_dir, load_mode, results_path
from experiments.reconstruct_game import reconstruct_states
from experiments.run_mode import run_pair

from create_corrected_modes import SOURCE_MODES


MODES = [f"corrected_{name}" for name in SOURCE_MODES]
PROGRESS = ROOT / "final_results" / "corrected_run_progress.json"


def nonself_pairs(mode: dict) -> list[tuple[str, str]]:
    names = [entry["name"] for entry in mode["agents"]]
    return [(a, b) for a in names for b in names if a != b]


def pair_complete(mode: dict, a: str, b: str) -> bool:
    result = results_path(mode["mode_name"], a, b)
    if not result.exists():
        return False
    with result.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    expected = len(mode["game_seeds"])
    if len(rows) != expected:
        return False
    directory = games_dir(mode["mode_name"], a, b)
    return all((directory / f"{index}.csv").exists() for index in range(expected))


def write_progress(completed_pairs: int, total_pairs: int, validated_games: int, elapsed: float) -> None:
    PROGRESS.parent.mkdir(parents=True, exist_ok=True)
    PROGRESS.write_text(json.dumps({
        "implementation_revision": "public_information_adversarial_v2",
        "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "completed_pairs": completed_pairs,
        "total_pairs": total_pairs,
        "validated_games": validated_games,
        "elapsed_seconds_this_run": elapsed,
    }, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    modes = [load_mode(name) for name in MODES]
    total_pairs = sum(len(nonself_pairs(mode)) for mode in modes)
    completed_pairs = 0
    validated_games = 0
    started = perf_counter()

    for mode_index, mode in enumerate(modes, 1):
        pairs = nonself_pairs(mode)
        print(f"MODE {mode_index}/{len(modes)} {mode['mode_name']} ({len(pairs)} pairs)", flush=True)
        for pair_index, (a, b) in enumerate(pairs, 1):
            if pair_complete(mode, a, b):
                status = "existing"
            else:
                pair_started = perf_counter()
                run_pair(mode, a, b)
                status = f"ran {perf_counter() - pair_started:.1f}s"

            for game_index in range(len(mode["game_seeds"])):
                reconstruct_states(mode, a, b, game_index, validate=True)
                validated_games += 1
            completed_pairs += 1
            elapsed = perf_counter() - started
            write_progress(completed_pairs, total_pairs, validated_games, elapsed)
            print(
                f"  {pair_index:02}/{len(pairs):02} {a}_vs_{b}: {status}; "
                f"validated={validated_games}; elapsed={elapsed / 3600:.2f}h",
                flush=True,
            )

    print(
        f"COMPLETE pairs={completed_pairs}/{total_pairs} "
        f"validated_games={validated_games} elapsed={(perf_counter() - started) / 3600:.2f}h",
        flush=True,
    )


if __name__ == "__main__":
    main()
