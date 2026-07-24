# Future-experiment results index

Start with [01_ANALYSIS.md](01_ANALYSIS.md). This package contains exploratory results from 1,206 new games. Minimax is excluded; timing is measured natively per agent and decision.

## Files

- [01_ANALYSIS.md](01_ANALYSIS.md) — Interpretation, limitations, and confirmatory recommendations
- [figures/01_board_designs.png](figures/01_board_designs.png) — Visual map of the four board geometries
- [figures/02_rule_vs_greedy_factors.png](figures/02_rule_vs_greedy_factors.png) — Rule–greedy robustness across factors
- [figures/03_deadlocks_by_factor.png](figures/03_deadlocks_by_factor.png) — Absorbing-market deadlock rates
- [figures/04_search_agents_boards.png](figures/04_search_agents_boards.png) — Search-agent strength and runtime across boards
- [figures/05_search_agents_pieces.png](figures/05_search_agents_pieces.png) — Search-agent strength and runtime by piece count
- [figures/05b_search_agents_decks.png](figures/05b_search_agents_decks.png) — Search-agent strength and runtime by deck
- [figures/06_expectimax_depth_tradeoff.png](figures/06_expectimax_depth_tradeoff.png) — Expectimax strength–depth–runtime trade-off
- [figures/07_mcts_budget_heatmaps.png](figures/07_mcts_budget_heatmaps.png) — MCTS budget strength and runtime heatmaps
- [figures/08_two_pass_refresh_effect.png](figures/08_two_pass_refresh_effect.png) — Matched validation of the selected market-refresh rule
- [figures/09_spread_spawn_boards.png](figures/09_spread_spawn_boards.png) — Four ring/orbit spawn and objective designs
- [figures/10_point_goal_results.png](figures/10_point_goal_results.png) — Time-to-goal and search-agent outcomes
- [figures/11_expectimax_depth_2_to_6_feasibility.png](figures/11_expectimax_depth_2_to_6_feasibility.png) — Measured feasibility boundary for depths 2-6
- [figures/12_net_launcher_usage.png](figures/12_net_launcher_usage.png) — Adjacent versus net-launcher captures by agent
- [tables/01_fast_rule_greedy.csv](tables/01_fast_rule_greedy.csv) — Direct rule–greedy factor results
- [tables/02_deadlocks.csv](tables/02_deadlocks.csv) — Deadlock summary by fast-screen factor
- [tables/03_search_factors.csv](tables/03_search_factors.csv) — Search-agent outcomes and measured runtime
- [tables/04_expectimax_depth.csv](tables/04_expectimax_depth.csv) — Expectimax depth screen
- [tables/05_mcts_budget.csv](tables/05_mcts_budget.csv) — MCTS parameter grid
- [tables/06_all_fast_results.csv](tables/06_all_fast_results.csv) — Raw aggregate results from fast-screen modes
- [tables/07_all_search_results.csv](tables/07_all_search_results.csv) — Raw aggregate results from search-screen modes
- [tables/08_refresh_rule_comparison.csv](tables/08_refresh_rule_comparison.csv) — Matched deadlock/draw comparison
- [tables/09_refresh_search_comparison.csv](tables/09_refresh_search_comparison.csv) — Search-agent results under original and refreshed markets
- [tables/10_spread_point_goal_results.csv](tables/10_spread_point_goal_results.csv) — Raw point-goal results on spread-spawn boards
- [tables/11_spread_point_goal_summary.csv](tables/11_spread_point_goal_summary.csv) — Time-to-goal summary by geometry and objective
- [tables/12_spread_search_agents.csv](tables/12_spread_search_agents.csv) — Search-agent outcomes on inner-ring objective variants
- [tables/13_net_launcher_usage.csv](tables/13_net_launcher_usage.csv) — Net and adjacent capture counts by agent
- [tables/14_expectimax_depth_2_to_6.csv](tables/14_expectimax_depth_2_to_6.csv) — Benchmark and bounded-match feasibility evidence
- [../../analysis/future_experiments_report.py](../../analysis/future_experiments_report.py) — Reproduction script

## Experimental tiers

- Fast robustness screens: 8 seeds, both orientations, 50 turns/player except explicit horizon modes.
- Search factor screens: 3 seeds, both orientations, 25 turns/player, expectimax depth 2/top-k 6, MCTS 100 simulations/depth 10.
- Budget screens: 3 seeds, both orientations, 15 turns/player.

These are screening samples. Use them to select confirmatory experiments, not as final precise rankings.
