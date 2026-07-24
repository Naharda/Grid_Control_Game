# Follow-up experiment plan

## Purpose

The baseline establishes a ranking on one configuration, but it also exposes a pass-deadlock mechanism and a large compute-budget imbalance. The next phase should test robustness before making broad claims about algorithm quality.

## Recommended execution order

| Priority | Experiment | Values | Main question | Primary plots |
|---:|---|---|---|---|
| 1 | Chance-model correction | realized hidden order; adversarial draw; probability-weighted draw | How much of minimax's strength comes from seeing the concrete future deck? | win points, score margin, nodes/time |
| 2 | Pass-rule robustness | unchanged market (baseline); discard/redraw one card; refresh all three cards | Are rankings driven by absorbing illegal markets? | win points, deadlock rate, effective turns |
| 3 | Existing board | `default`; `crossfire` | Does a larger board with two unequal scoring cells change the ranking? | matchup matrix, scoring-source split |
| 4 | Equal compute | fixed per-move time budgets | Does search still help when computation is controlled? | win points vs time |
| 5 | Expectimax depth | 1, 2, 3; depth 4 only if feasible | Does exact chance expansion repay its exponential cost? | win points, ms/move, nodes/move |
| 6 | MCTS grid | simulations 50, 100, 200, 500, 1000 × rollout depth 5, 10, 20, 40 | Where are the diminishing returns? | heatmaps for strength and time |
| 7 | Deck mix | movement-heavy; balanced; capture-heavy; swap-heavy | Which action supply favors each planning method? | action profile, deadlocks, ranking |
| 8 | Piece count | 2, 3, 4 per player on compatible boards | How does branching and congestion affect agents? | strength/time Pareto frontier |
| 9 | Scoring/horizon | capture score 1, 3, 5; 25, 50, 75 turns/player | Is the ranking stable under strategic incentives and horizon? | win points, score source, trajectories |

## Minimal confirmatory design

- Run every ordered non-self pair in both orientations.
- Use the same 100 game seeds per orientation for every configuration.
- Treat seed as a paired/blocking variable when comparing configurations or move order.
- Keep the baseline configuration unchanged as a control in every batch.
- Record wall-clock decision time and search nodes/simulations per turn.
- Record legal-action count, pass events, final pass streak, selected card, capture mode, and score increment.
- Report win points (win=1, draw=0.5), score margin, and deadlock rate as co-primary practical outcomes.
- Use confidence intervals and effect sizes; do not rely only on null-hypothesis tests.

With six agents, a full ordered round-robin has 30 non-self ordered pairs. At 100 seeds, that is 3,000 games per configuration. Parameter sweeps can become expensive quickly, so first screen configurations with 20 seeds and then rerun only predeclared promising settings with 100 seeds. Do not use the screening games again as confirmatory evidence.

## Configuration notes

### Boards and piece counts

`boards/crossfire.json` already provides a 5×7 board with 1-point and 2-point scoring cells plus a blocked center segment. Piece count is encoded by the number of spawn positions in a board JSON file, so 2-piece and 4-piece tests require new board definitions with matching A/B spawn lists. Keep boards symmetric unless asymmetry is the factor being studied.

### Deck composition

Keep total deck size at 28 for the first comparison so only proportions change. Suggested compositions:

| Deck | move1 | move2 | mobilize | capture | swap |
|---|---:|---:|---:|---:|---:|
| balanced baseline | 8 | 6 | 5 | 5 | 4 |
| movement-heavy | 10 | 8 | 6 | 2 | 2 |
| capture-heavy | 5 | 4 | 4 | 11 | 4 |
| swap-heavy | 6 | 5 | 4 | 4 | 9 |

The capture-heavy condition must be paired with the pass-rule robustness test: otherwise increased deadlocks may be mistaken for strategic behavior.

### Point requirements and win conditions

The current engine ends after a fixed number of turns and awards the win to the higher score. `--turns` and `--capture-score` are already configurable. A “first to N points” condition is not currently a mode parameter; it is a different termination rule and requires an engine/config change plus tests. Treat it as a separate ruleset, and report turns-to-finish alongside win rate because match duration becomes endogenous.

### Search budgets

Use the existing mode parameter interface for expectimax and MCTS, for example:

```powershell
python src/experiments/create_mode.py expectimax_d3 --agents expectimax rule --num-games 100 --param expectimax.depth=3
python src/experiments/create_mode.py mcts_s500_r20 --agents mcts rule --num-games 100 --param mcts.simulations=500 --param mcts.rollout_depth=20
```

Before launching a large sweep, time one complete game at the largest setting. Expectimax cost can grow sharply with depth because it expands both action and chance branches.

## Analysis model for the final report

For win/loss/draw outcomes, use a paired seed analysis or a mixed-effects/clustered model with agent, seat, configuration, and their interactions; cluster on seed and matchup. For score margin and runtime, show medians as well as means because both may be skewed. The central report claim should be an interaction claim—whether an agent remains strong across boards, decks, and budgets—not just a single baseline ranking.
