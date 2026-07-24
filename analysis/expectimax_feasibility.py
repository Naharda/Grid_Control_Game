"""Bounded one-decision feasibility benchmark for expectimax depths 2--6."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from game.rules import get_legal_actions
from game.setup_loader import build_config, load_board
from game.state import initial_state
from search.expectimax import choose_expectimax


def child(depth: int) -> None:
    config = build_config(
        board=load_board("inner_ring_center_7x7"),
        seed=0,
        turns_per_player=15,
        capture_score=1,
        market_refresh_after_passes=2,
        score_to_win=40,
    )
    state = initial_state(config)
    started = time.perf_counter()
    _, stats = choose_expectimax(state, depth=depth, player="A", top_k=3)
    print(
        json.dumps(
            {
                "depth": depth,
                "top_k": 3,
                "seconds": time.perf_counter() - started,
                "nodes": stats.nodes,
                "legal_actions": len(get_legal_actions(state)),
                "status": "completed",
            }
        )
    )


def parent(timeout: int) -> None:
    results = []
    for depth in range(2, 7):
        started = time.perf_counter()
        try:
            completed = subprocess.run(
                [sys.executable, str(Path(__file__).resolve()), "--child", str(depth)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
                check=True,
            )
            results.append(json.loads(completed.stdout.strip()))
        except subprocess.TimeoutExpired:
            results.append(
                {
                    "depth": depth,
                    "top_k": 3,
                    "seconds": time.perf_counter() - started,
                    "nodes": None,
                    "legal_actions": None,
                    "status": f"timeout>{timeout}s",
                }
            )
            # Deeper searches cannot be more feasible under the same branching setup.
            for skipped in range(depth + 1, 7):
                results.append(
                    {
                        "depth": skipped,
                        "top_k": 3,
                        "seconds": None,
                        "nodes": None,
                        "legal_actions": None,
                        "status": "skipped_after_shallower_timeout",
                    }
                )
            break
    print(json.dumps(results, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--child", type=int)
    parser.add_argument("--timeout", type=int, default=120)
    args = parser.parse_args()
    if args.child is not None:
        child(args.child)
    else:
        parent(args.timeout)


if __name__ == "__main__":
    main()
