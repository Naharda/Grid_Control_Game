"""Replay and validate every game in the corrected reduced-factorial suite."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from experiments.modes import load_mode
from experiments.reconstruct_game import reconstruct_states

from reduced_factorial_report import ALL_MODES


def main() -> None:
    checked = 0
    for mode_name in ALL_MODES:
        mode = load_mode(mode_name)
        for pair_dir in sorted((ROOT / "modes" / mode_name / "games").iterdir()):
            if not pair_dir.is_dir():
                continue
            agent_a, agent_b = None, None
            names = [entry["name"] for entry in mode["agents"]]
            for candidate in names:
                prefix = f"{candidate}_"
                if pair_dir.name.startswith(prefix) and pair_dir.name[len(prefix):] in names:
                    agent_a, agent_b = candidate, pair_dir.name[len(prefix):]
                    break
            if agent_a is None or agent_b is None:
                raise ValueError(f"Cannot parse pair directory {pair_dir}")
            for game_path in sorted(pair_dir.glob("*.csv"), key=lambda p: int(p.stem)):
                reconstruct_states(mode, agent_a, agent_b, int(game_path.stem), validate=True)
                checked += 1
    if checked != 1116:
        raise ValueError(f"Expected 1116 validated games, got {checked}")
    print(f"Validated {checked} game logs and result rows.")


if __name__ == "__main__":
    main()
