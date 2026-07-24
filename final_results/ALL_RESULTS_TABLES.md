# Consolidated results tables

This file summarizes every completed experiment family. Win points use
`win = 1`, `draw = 0.5`, `loss = 0`. Small screening samples are exploratory,
not confirmatory. The linked CSV files retain the complete precision and
individual rows.

## 0. Reduced factorial suite (current primary experiment)

This is the current internally consistent suite: all 846 games use the
two-consecutive-pass market refresh, native runtime logging, and net-launcher
statistics. The main/deck matrix uses all 30 ordered non-self pairs and three
matched seeds per condition.

| Agent | Main-suite games | Win points | First-seat WP | Second-seat WP | Weighted ms/decision |
|---|---:|---:|---:|---:|---:|
| Rule | 270 | 75.4% | 78.5% | 72.2% | 7.2 |
| MCTS | 270 | 61.7% | 63.0% | 60.4% | 209.5 |
| Expectimax d3 | 270 | 57.6% | 61.5% | 53.7% | 1,335.3 |
| Expectimax d2 | 270 | 54.3% | 54.8% | 53.7% | 176.3 |
| Greedy | 270 | 51.1% | 51.9% | 50.4% | 15.3 |
| Random | 270 | 0.0% | 0.0% | 0.0% | 0.004 |

Full package: [reduced factorial index](reduced_factorial/00_INDEX.md),
[coverage manifest](reduced_factorial/tables/01_coverage_manifest.csv),
[board and goal results](reduced_factorial/tables/02_board_goal_agent_performance.csv),
[independent deck results](reduced_factorial/tables/04_deck_agent_performance.csv),
and [net-launcher results](reduced_factorial/tables/07_net_launcher_usage.csv).

## 1. Baseline full: overall agent performance

The baseline contains 1,080 games. The table excludes self-play when computing
competitive performance; each agent therefore has 300 opponent-game
observations.

| Agent | Games | W-D-L | Win points | Mean margin | Median benchmark ms/decision |
|---|---:|---:|---:|---:|---:|
| Rule | 300 | 230-19-51 | 79.8% | +25.96 | 1.169 |
| Minimax* | 300 | 199-20-81 | 69.7% | +20.28 | 101.100 |
| Expectimax | 300 | 192-23-85 | 67.8% | +18.97 | 1,158.168 |
| MCTS | 300 | 130-30-140 | 48.3% | +6.91 | 684.028 |
| Greedy | 300 | 75-18-207 | 28.0% | -10.27 | 10.725 |
| Random | 300 | 3-32-265 | 6.3% | -61.85 | 0.0005 |

\*The minimax result is not valid evidence about stochastic minimax: it does
not expand chance nodes and can inspect the realized deck order.

Full tables: [overall performance](baseline_full/tables/01_agent_performance.csv),
[first/second seat results](baseline_full/tables/02_seat_performance.csv),
[head-to-head details](baseline_full/tables/05_matchup_detail.csv), and
[strategy metrics](baseline_full/tables/09_strategy_metrics.csv).

## 2. Fast robustness screens: direct rule versus greedy

Each row contains 16 direct rule-greedy games (8 paired seeds in both
orientations). The wider screen contains 48 games per condition because it also
includes random.

| Family | Condition | Rule win points | Greedy win points | Rule mean margin | Deadlocks in all 48 |
|---|---|---:|---:|---:|---:|
| Board | Default 5x5 | 100.0% | 0.0% | +38.50 | 12.5% |
| Board | Dual arena 5x7 | 50.0% | 50.0% | -0.88 | 43.8% |
| Board | Open 7x7 | 37.5% | 62.5% | +1.19 | 62.5% |
| Board | Bottleneck 7x7 | 46.9% | 53.1% | +7.94 | 68.8% |
| Pieces | 2 pieces | 71.9% | 28.1% | +10.19 | 45.8% |
| Pieces | 4 pieces | 96.9% | 3.1% | +41.38 | 10.4% |
| Deck | Movement-heavy | 100.0% | 0.0% | +42.13 | 0.0% |
| Deck | Capture-heavy | 81.3% | 18.8% | +37.38 | 83.3% |
| Deck | Swap-heavy | 93.8% | 6.3% | +39.13 | 18.8% |
| Scoring | Capture = 1 | 100.0% | 0.0% | +41.63 | 16.7% |
| Scoring | Capture = 5 | 93.8% | 6.3% | +36.13 | 12.5% |
| Horizon | 25 turns/player | 87.5% | 12.5% | +16.63 | 12.5% |
| Horizon | 75 turns/player | 100.0% | 0.0% | +54.56 | 14.6% |

Full tables: [rule-greedy results](future_experiments/tables/01_fast_rule_greedy.csv)
and [deadlocks](future_experiments/tables/02_deadlocks.csv).

## 3. Search-agent factor screens

Each agent has 12 observations per condition: two opponents, both orientations,
and three seeds. Runtime is weighted milliseconds per actual non-pass decision.

| Family | Condition | Rule WP / ms | Expectimax WP / ms | MCTS WP / ms |
|---|---|---:|---:|---:|
| Board | Default 5x5 | 58.3% / 3.9 | 41.7% / 507.5 | 50.0% / 167.5 |
| Board | Dual arena 5x7 | 54.2% / 6.8 | 29.2% / 502.2 | 66.7% / 161.0 |
| Board | Open 7x7 | 29.2% / 7.8 | 45.8% / 508.9 | 75.0% / 123.3 |
| Board | Bottleneck 7x7 | 37.5% / 6.0 | 62.5% / 437.0 | 50.0% / 108.0 |
| Pieces | 2 pieces | 54.2% / 1.7 | 33.3% / 252.9 | 62.5% / 103.3 |
| Pieces | 4 pieces | 91.7% / 7.0 | 12.5% / 610.9 | 45.8% / 190.5 |
| Deck | Movement-heavy | 91.7% / 6.5 | 0.0% / 552.0 | 58.3% / 196.4 |
| Deck | Capture-heavy | 50.0% / 2.1 | 41.7% / 401.0 | 58.3% / 98.1 |
| Deck | Swap-heavy | 91.7% / 3.8 | 41.7% / 448.5 | 16.7% / 154.5 |

Full table: [search-factor results](future_experiments/tables/03_search_factors.csv).

## 4. Market-refresh rule

| Environment | Pass rule | Games | Draws | Deadlocks | Mean total score |
|---|---|---:|---:|---:|---:|
| Default | Original | 48 | 6.3% | 12.5% | 89.85 |
| Default | Refresh after 2 passes | 48 | 0.0% | 0.0% | 100.56 |
| Capture-heavy | Original | 48 | 33.3% | 83.3% | 50.25 |
| Capture-heavy | Refresh after 2 passes | 48 | 0.0% | 0.0% | 141.10 |

Search-agent results on the capture-heavy deck:

| Rule | Agent | Games | Win points | Mean margin | ms/decision |
|---|---|---:|---:|---:|---:|
| Original | Rule | 12 | 50.0% | +1.33 | 2.1 |
| Original | Expectimax | 12 | 41.7% | +0.50 | 401.0 |
| Original | MCTS | 12 | 58.3% | -1.83 | 98.1 |
| Refresh after 2 passes | Rule | 12 | 70.8% | +6.58 | 3.7 |
| Refresh after 2 passes | Expectimax | 12 | 29.2% | -3.17 | 654.4 |
| Refresh after 2 passes | MCTS | 12 | 50.0% | -3.42 | 171.3 |

Full tables: [matched rule comparison](future_experiments/tables/08_refresh_rule_comparison.csv)
and [search-agent comparison](future_experiments/tables/09_refresh_search_comparison.csv).

## 5. Expectimax parameter results

Initial six-game budget screen against rule:

| Depth | Top-k | Games | Win points | Mean margin | ms/decision |
|---:|---:|---:|---:|---:|---:|
| 1 | 4 | 6 | 25.0% | -9.83 | 18.4 |
| 2 | 4 | 6 | 16.7% | -8.17 | 272.2 |
| 3 | 4 | 6 | 66.7% | -1.67 | 3,730.2 |

Depth 2-6 feasibility benchmark:

| Depth | Single-decision time | Nodes | Bounded games | Bounded win points | Bounded ms/decision | Status |
|---:|---:|---:|---:|---:|---:|---|
| 2 | 1.166 s | 240 | 2 | 50.0% | 323.0 | Completed |
| 3 | 10.274 s | 3,615 | 2 | 100.0% | 1,990.5 | Completed |
| 4 | 102.444 s | 53,545 | 2 | 100.0% | 18,004.6 | Completed |
| 5 | >120 s | — | 0 | — | — | Timed out |
| 6 | — | — | 0 | — | — | Skipped after depth-5 timeout |

Full tables: [initial depth screen](future_experiments/tables/04_expectimax_depth.csv)
and [depth 2-6 feasibility](future_experiments/tables/14_expectimax_depth_2_to_6.csv).

## 6. MCTS parameter results

Each setting contains six games against rule.

| Simulations | Rollout depth | Win points | Mean margin | ms/decision |
|---:|---:|---:|---:|---:|
| 50 | 5 | 41.7% | -0.33 | 56.8 |
| 50 | 10 | 8.3% | -6.00 | 76.7 |
| 50 | 20 | 33.3% | -4.67 | 95.5 |
| 100 | 5 | 33.3% | -3.33 | 109.0 |
| 100 | 10 | 41.7% | +0.33 | 150.0 |
| 100 | 20 | 66.7% | +4.67 | 179.4 |
| 200 | 5 | 16.7% | -4.50 | 217.2 |
| 200 | 10 | 75.0% | +3.83 | 282.5 |
| 200 | 20 | 66.7% | +1.33 | 358.6 |

Full table: [MCTS budget grid](future_experiments/tables/05_mcts_budget.csv).

## 7. Spread-spawn and point-goal results

All 192 fast-agent games reached the score goal and had a decisive winner.

| Geometry | Objectives | Goal | Games | Mean combined turns | Median combined turns | Mean winning score |
|---|---|---:|---:|---:|---:|---:|
| Inner ring | Distributed | 40 | 48 | 32.75 | 33.5 | 40.90 |
| Inner ring | Single center | 40 | 48 | 23.48 | 22.0 | 41.44 |
| Outer orbit | Distributed | 60 | 48 | 27.42 | 27.0 | 61.92 |
| Outer orbit | Single center | 60 | 48 | 26.81 | 25.5 | 62.44 |

Inner-ring search-agent screen:

| Objectives | Agent | Games | Win points | Mean margin | ms/decision |
|---|---|---:|---:|---:|---:|
| Single center | Rule | 12 | 50.0% | -0.17 | 8.4 |
| Single center | Expectimax | 12 | 50.0% | -1.17 | 958.7 |
| Single center | MCTS | 12 | 50.0% | +1.33 | 244.6 |
| Distributed | Rule | 12 | 58.3% | +4.33 | 22.0 |
| Distributed | Expectimax | 12 | 66.7% | +3.58 | 1,134.4 |
| Distributed | MCTS | 12 | 25.0% | -7.92 | 300.2 |

Full tables: [all point-goal games](future_experiments/tables/10_spread_point_goal_results.csv),
[condition summary](future_experiments/tables/11_spread_point_goal_summary.csv), and
[search-agent results](future_experiments/tables/12_spread_search_agents.csv).

## 8. Net-launcher usage

These counts cover the 228 spread-board fast/search games and exclude the six
bounded-depth duplicates.

| Agent | Adjacent captures | Net launches | Total captures | Net share |
|---|---:|---:|---:|---:|
| Expectimax | 58 | 10 | 68 | 14.7% |
| Greedy | 256 | 72 | 328 | 22.0% |
| MCTS | 56 | 13 | 69 | 18.8% |
| Random | 178 | 104 | 282 | 36.9% |
| Rule | 325 | 62 | 387 | 16.0% |
| **Total** | **873** | **261** | **1,134** | **23.0%** |

Full table: [net-launcher usage](future_experiments/tables/13_net_launcher_usage.csv).

## Data coverage

| Package | Games |
|---|---:|
| Baseline full | 1,080 |
| Follow-up experiments | 1,206 |
| Reduced factorial suite | 846 |
| **Total games run** | **3,132** |

The individual-game aggregate result rows are available in
[baseline matchup details](baseline_full/tables/05_matchup_detail.csv),
[all fast follow-up results](future_experiments/tables/06_all_fast_results.csv),
[all search follow-up results](future_experiments/tables/07_all_search_results.csv),
and [all spread point-goal results](future_experiments/tables/10_spread_point_goal_results.csv).
