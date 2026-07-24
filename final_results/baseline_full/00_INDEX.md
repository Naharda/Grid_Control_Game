# Baseline Full final-results index

This folder is the report-ready output for `modes/baseline_full`. Files are numbered in recommended reading order. Start with [01_ANALYSIS.md](01_ANALYSIS.md).

## At-a-glance ranking

1. **rule** — 79.8% win points, +25.96 mean margin, 1.169 ms median benchmark decision
2. **minimax** — 69.7% win points, +20.28 mean margin, 101.100 ms median benchmark decision
3. **expectimax** — 67.8% win points, +18.97 mean margin, 1158.168 ms median benchmark decision
4. **mcts** — 48.3% win points, +6.91 mean margin, 684.028 ms median benchmark decision
5. **greedy** — 28.0% win points, -10.27 mean margin, 10.725 ms median benchmark decision
6. **random** — 6.3% win points, -61.85 mean margin, 0.0005 ms median benchmark decision

## Files

- [01_ANALYSIS.md](01_ANALYSIS.md) — Main report-ready interpretation, limitations, and follow-up design
- [02_FOLLOW_UP_EXPERIMENTS.md](02_FOLLOW_UP_EXPERIMENTS.md) — Prioritized experiment matrix and confirmatory design
- [figures/01_overall_performance.png](figures/01_overall_performance.png) — Competitive win points and mean score margin
- [figures/02_first_vs_second.png](figures/02_first_vs_second.png) — Agent performance split by move order
- [figures/03_head_to_head.png](figures/03_head_to_head.png) — Combined-orientation matchup matrix
- [figures/04_runtime_vs_performance.png](figures/04_runtime_vs_performance.png) — Post-hoc decision-time/performance trade-off
- [figures/05_action_profiles.png](figures/05_action_profiles.png) — Selected card distribution on non-pass turns
- [figures/06_scoring_sources.png](figures/06_scoring_sources.png) — Capture versus scoring-cell control points
- [figures/07_score_trajectories.png](figures/07_score_trajectories.png) — Mean cumulative score by personal turn
- [figures/08_passes_and_deadlocks.png](figures/08_passes_and_deadlocks.png) — Pass frequency and absorbing-market deadlocks
- [tables/01_agent_performance.csv](tables/01_agent_performance.csv) — Overall competitive ranking with bootstrap intervals
- [tables/02_seat_performance.csv](tables/02_seat_performance.csv) — First/second descriptive statistics
- [tables/03_paired_seat_effects.csv](tables/03_paired_seat_effects.csv) — Paired-seed first-minus-second estimates
- [tables/04_head_to_head_win_points.csv](tables/04_head_to_head_win_points.csv) — Head-to-head matrix values
- [tables/05_matchup_detail.csv](tables/05_matchup_detail.csv) — Wins, draws, losses, and margins for every matchup
- [tables/06_runtime_benchmark.csv](tables/06_runtime_benchmark.csv) — Runtime benchmark summary
- [tables/07_runtime_benchmark_raw.csv](tables/07_runtime_benchmark_raw.csv) — Per-state runtime measurements and node counts
- [tables/08_action_profiles.csv](tables/08_action_profiles.csv) — Action choices and market-exposure normalization
- [tables/09_strategy_metrics.csv](tables/09_strategy_metrics.csv) — Scoring sources, captures, net use, passes, deadlocks
- [tables/10_score_trajectories.csv](tables/10_score_trajectories.csv) — Plot-ready score trajectory values
- [tables/11_game_level_strategy.csv](tables/11_game_level_strategy.csv) — Agent-game strategy observations
- [../../analysis/baseline_full_report.py](../../analysis/baseline_full_report.py) — Reproduction script

## Metric conventions

- Self-play is excluded from competitive performance and seat comparisons.
- A win is 1 win point, a draw 0.5, and a loss 0.
- Head-to-head cells combine both orientations and contain 60 games.
- Error intervals are game-level percentile bootstrap 95% intervals with a fixed seed.
- Runtime is a post-hoc same-state benchmark because the original experiment did not log time.
- A game is flagged as deadlocked when its final 10 or more scheduled turns are passes.
