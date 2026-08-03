"""Clone the final legacy experiment definitions for corrected-agent reruns."""

from __future__ import annotations

import copy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from experiments.modes import load_mode, save_mode


SOURCE_MODES = [
    "reduced_board_default_fixed_r2",
    "reduced_board_default_goal10_r2",
    "reduced_board_default_goal40_r2",
    "reduced_board_bottleneck_7x7_fixed_r2",
    "reduced_board_bottleneck_7x7_goal10_r2",
    "reduced_board_bottleneck_7x7_goal40_r2",
    "reduced_board_inner_ring_center_7x7_fixed_r2",
    "reduced_board_inner_ring_center_7x7_goal10_r2",
    "reduced_board_inner_ring_center_7x7_goal40_r2",
    "reduced_deck_movement_heavy_fixed_r2",
    "reduced_deck_capture_heavy_fixed_r2",
    "reduced_deck_swap_heavy_fixed_r2",
    "reduced_depth_default_goal20_r2",
    "reduced_depth_bottleneck_7x7_goal20_r2",
    "reduced_depth_inner_ring_center_7x7_goal20_r2",
]

REVISION = {
    "name": "public_information_adversarial_v2",
    "changes": [
        "agent action ranking is invariant to hidden deck order",
        "expectimax beam ordering minimizes at opponent nodes",
        "MCTS samples public chance outcomes with an agent-local RNG",
        "MCTS selects opponent nodes adversarially",
    ],
}


def corrected_mode(source_name: str) -> dict:
    mode = copy.deepcopy(load_mode(source_name))
    mode["mode_name"] = f"corrected_{source_name}"
    mode["description"] = f"Corrected public-information rerun of {source_name}"
    mode["implementation_revision"] = REVISION
    mode["source_mode"] = source_name
    return mode


def main() -> None:
    for source_name in SOURCE_MODES:
        mode = corrected_mode(source_name)
        path = save_mode(mode)
        print(path)

    pilot = corrected_mode("reduced_board_default_fixed_r2")
    pilot["mode_name"] = "corrected_pilot_default_fixed"
    pilot["description"] = "One-seed pilot for corrected public-information agents"
    pilot["game_seeds"] = pilot["game_seeds"][:1]
    pilot["num_games"] = 1
    print(save_mode(pilot))


if __name__ == "__main__":
    main()
