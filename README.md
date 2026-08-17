# Graph Card Control

Small stochastic, perfect-information, turn-based abstract game for Search Methods in AI experiments.

The final report is [`graph_card_control_final_report.pdf`](graph_card_control_final_report.pdf); its figures and source tables live under [`final_results/`](final_results/00_INDEX.md).

## Quick Start

Use Python 3.10+ (`pip install -r requirements.txt`).

```bash
python start_game.py --a human --b greedy --show-initial
python start_game.py --gui --a human --b greedy
python src/experiments/run_match.py --a greedy --b random --show-initial
pytest
```

## Game modes (experiments)

An experiment is a **game mode**: a reproducible bundle of board, deck, rules,
agents (with hyperparameters), and per-game seeds, defined *before* running.

```bash
# 1. Define a mode (refuses to overwrite an existing one; try --interactive)
python src/experiments/create_mode.py baseline --agents greedy minimax --games 20
#    ...or pit every non-human agent against each other:
python src/experiments/create_mode.py full --all-agents --games 20

# 2. Run every ordered agent pair (A-vs-B and B-vs-A share seeds per game index)
python src/experiments/run_mode.py baseline

# 3. Analyze a pair's results
python src/experiments/analyze_results.py modes/baseline/results/greedy_minimax.csv

# 4. Replay + validate any recorded game (optionally in the GUI)
python src/experiments/reconstruct_game.py baseline greedy minimax 0 --gui

# Play a mode yourself; --record saves your game in the same CSV format
python start_game.py --gui --mode baseline --a human --record
```

Outputs land in `modes/<name>/results/<a>_<b>.csv` (winner + scores per game)
and `modes/<name>/games/<a>_<b>/<i>.csv` (full per-turn move log). Boards and
decks are JSON files under `boards/` and `decks/` — boards define dimensions,
spawn cells, blocked cells, and *capture cells* (each granting configurable
points per turn of occupancy; the default board has one 1-point cell at the
center). See `boards/crossfire.json` for a custom example.

## Implemented

- Configurable grid board (JSON): dimensions, spawns, blocked cells, weighted capture cells.
- Shared ordered deck (JSON composition), public 3-card market, discard reshuffle.
- Move 1, Move 2, Mobilize, Capture/Net Launcher, and Swap.
- Deterministic captured-piece spawn fallback.
- Random, rule-based, greedy, human text, minimax, expectimax, and MCTS agents.
- Tactical greedy best-first, A*, and bidirectional search toward capture cells.
- Game modes: reproducible experiment configs, per-game move logs, replay/validation, GUI review.
- Text renderer and Pygame viewer with history review and capture-cell point labels.

## Pygame Controls

```bash
python start_game.py --gui --a human --b greedy
```

- Click a market card, then click the required pieces/cells.
- `Back` / `Next` buttons, or Left / Right keys, review the game history.
- `Space` advances the next reviewed/computer move.
- `Auto` button or `A` toggles automatic computer play.
- `Clear` button or `Esc` clears the current selection.

The full rules are in [`Instructions.md`](Instructions.md); all numeric values are `GameConfig` defaults, configurable per board/deck/mode.
