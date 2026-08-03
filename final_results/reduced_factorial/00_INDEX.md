# Reduced factorial results

Start with [01_ANALYSIS.md](01_ANALYSIS.md). The suite contains 1,116 games, uses the two-pass market refresh throughout, compares every planned ordered pair, and includes net-launcher statistics.

## Files

- [01_ANALYSIS.md](01_ANALYSIS.md) — Interpretation and limitations
- [figures/01_board_goal_performance.png](figures/01_board_goal_performance.png) — Agent performance by board and end condition
- [figures/02_agent_order.png](figures/02_agent_order.png) — First-versus-second comparison
- [figures/03_deck_performance.png](figures/03_deck_performance.png) — Independent deck-composition results
- [figures/04_expectimax_depths.png](figures/04_expectimax_depths.png) — Direct depth comparison and bounded runtime
- [figures/05_runtime_performance.png](figures/05_runtime_performance.png) — Performance-runtime trade-off
- [figures/06_net_launcher_usage.png](figures/06_net_launcher_usage.png) — Adjacent versus net captures
- [tables/01_coverage_manifest.csv](tables/01_coverage_manifest.csv) — Proof of complete planned coverage
- [tables/02_board_goal_agent_performance.csv](tables/02_board_goal_agent_performance.csv) — Board/end-condition agent results
- [tables/03_agent_order.csv](tables/03_agent_order.csv) — First and second seat results
- [tables/04_deck_agent_performance.csv](tables/04_deck_agent_performance.csv) — Independent deck results
- [tables/05_expectimax_d2_vs_d3.csv](tables/05_expectimax_d2_vs_d3.csv) — Direct depth-2 versus depth-3 results
- [tables/06_bounded_depth_performance.csv](tables/06_bounded_depth_performance.csv) — Depths 2-4 bounded comparison
- [tables/07_net_launcher_usage.csv](tables/07_net_launcher_usage.csv) — Net usage by agent
- [tables/08_net_capture_events.csv](tables/08_net_capture_events.csv) — Capture-event source data
- [tables/09_board_goal_game_length.csv](tables/09_board_goal_game_length.csv) — Game length and score by end condition
- [tables/10_all_main_results.csv](tables/10_all_main_results.csv) — All 810 main/deck result rows
- [tables/11_all_bounded_depth_results.csv](tables/11_all_bounded_depth_results.csv) — All 36 bounded depth rows
- [../../analysis/reduced_factorial_report.py](../../analysis/reduced_factorial_report.py) — Reproduction script
- [../../analysis/validate_reduced_factorial.py](../../analysis/validate_reduced_factorial.py) — Full replay validator
