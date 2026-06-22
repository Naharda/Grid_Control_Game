from __future__ import annotations

import argparse
import csv
from collections import Counter


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_file")
    args = parser.parse_args()

    with open(args.csv_file, newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    wins = Counter(row["winner"] for row in rows)
    diffs = [int(row["score_a"]) - int(row["score_b"]) for row in rows]
    avg_diff = sum(diffs) / len(diffs) if diffs else 0.0
    print(f"Games: {len(rows)}")
    print(f"Wins: {dict(wins)}")
    print(f"Average A-B score diff: {avg_diff:.2f}")


if __name__ == "__main__":
    main()
