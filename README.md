# Graph Card Control

Small stochastic, perfect-information, turn-based abstract game for Search Methods in AI experiments.

## Quick Start

Use Python 3.10+.

```powershell
$env:PYTHONPATH='src'
python start_game.py --a human --b greedy --show-initial
python start_game.py --gui --a human --b greedy
python visual_game.py --a human --b greedy
python src/experiments/run_match.py --a greedy --b random --show-initial
python src/experiments/tournament.py --a expectimax --b greedy --games 20 --out results.csv
python src/experiments/analyze_results.py results.csv
pytest
```

## Implemented

- 5x5 graph-backed grid board with center scoring.
- Shared ordered deck, public 3-card market, discard reshuffle.
- Move 1, Move 2, Mobilize, Capture/Net Launcher, and Swap.
- Deterministic captured-piece spawn fallback.
- Random, rule-based, greedy, human text, minimax, expectimax, and MCTS agents.
- Tactical greedy best-first, A* to center, and bidirectional center helper.
- Text renderer, optional static Pygame viewer, match runner, tournament CSV output, and simple result analysis.

## Pygame Controls

```powershell
python visual_game.py --a human --b greedy
```

- Click a market card, then click the required pieces/cells.
- `Back` / `Next` buttons, or Left / Right keys, review the game history.
- `Space` advances the next reviewed/computer move.
- `Auto` button or `A` toggles automatic computer play.
- `Clear` button or `Esc` clears the current selection.

The default game rules follow the defaults listed in `graph_card_control_codex_plan.md`.
