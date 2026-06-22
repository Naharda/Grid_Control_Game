from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.run_match import build_agent
from game.config import GameConfig
from game.engine import play_match
from game.state import initial_state


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--a", default="greedy")
    parser.add_argument("--b", default="random")
    parser.add_argument("--games", type=int, default=20)
    parser.add_argument("--out", default="results.csv")
    args = parser.parse_args()

    rows = []
    wins = {"A": 0, "B": 0, "draw": 0}
    for game_id in range(args.games):
        state = initial_state(GameConfig(seed=game_id))
        result = play_match(build_agent(args.a), build_agent(args.b), state)
        wins[result.winner or "draw"] += 1
        rows.append(
            {
                "game": game_id,
                "agent_a": args.a,
                "agent_b": args.b,
                "winner": result.winner or "draw",
                "score_a": result.scores["A"],
                "score_b": result.scores["B"],
            }
        )

    with open(args.out, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {args.out}")
    print(wins)


if __name__ == "__main__":
    main()
