"""Audit whether agent choices depend on the stored order of the hidden deck.

The visible state and deck multiset are held fixed. Only the ordering of the
remaining deck is permuted. A public-information agent should not change its
choice solely because of this hidden implementation detail.
"""

from __future__ import annotations

import argparse
import csv
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from experiments.modes import config_from_mode, effective_agent_params, load_mode
from experiments.run_match import build_agent
from game.rules import apply_action, apply_pass, get_legal_actions
from game.state import initial_state


def audit() -> list[dict[str, str | int | float]]:
    mode = load_mode("reduced_board_default_fixed_r2")
    game_seed = mode["game_seeds"][0]
    state = initial_state(config_from_mode(mode, seed=game_seed))
    specs = {entry["name"]: entry["params"] for entry in mode["agents"]}

    trajectory_rng = random.Random(77)
    checkpoints = {2, 5, 8, 11, 14, 17, 20, 23, 26, 29, 32, 35}
    states = []
    for turn in range(36):
        legal = get_legal_actions(state)
        state = apply_action(state, trajectory_rng.choice(legal)) if legal else apply_pass(state)
        if turn in checkpoints and state.deck:
            states.append(state)

    rows: list[dict[str, str | int | float]] = []
    for name in ("greedy", "rule", "expectimax_d2", "mcts"):
        tested = states if name != "mcts" else states[:8]
        params = effective_agent_params(
            specs[name], mode.get("agent_seed_policy", "derived"), game_seed, 0
        )
        sensitive = 0
        unique_total = 0
        for state_index, checkpoint_state in enumerate(tested):
            choices = []
            for permutation in range(12):
                deck = list(checkpoint_state.deck)
                random.Random(10_000 + state_index * 100 + permutation).shuffle(deck)
                permuted = checkpoint_state.with_updates(deck=tuple(deck))
                agent = build_agent(name, params)
                choices.append(agent.choose_action(permuted, get_legal_actions(permuted)).compact())
            unique = len(set(choices))
            unique_total += unique
            sensitive += int(unique > 1)
        rows.append({
            "agent": name,
            "states_tested": len(tested),
            "deck_permutations_per_state": 12,
            "sensitive_states": sensitive,
            "sensitive_state_rate": sensitive / len(tested),
            "mean_unique_actions": unique_total / len(tested),
        })
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    rows = audit()
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    for row in rows:
        print(row)


if __name__ == "__main__":
    main()
