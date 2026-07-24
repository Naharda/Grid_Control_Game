# Future experiments: screening results

## Scope and status

This is an **exploratory screening study**, not the final confirmatory experiment. It contains **1,206 newly run games**:

- 624 fast-agent robustness games (`random`, `greedy`, `rule`) across boards, piece counts, decks, scoring values, and horizons;
- 162 targeted search-agent games (`rule`, `expectimax`, `mcts`) across boards, piece counts, and decks;
- 72 parameter games for expectimax depth and the MCTS simulations × rollout-depth grid.
- 114 matched games evaluating the selected two-pass market-refresh rule.
- 234 games covering spread-spawn boards, point-goal wins, and bounded expectimax depths 2-4.

The flawed minimax agent is excluded. Every new results row records the time spent by each agent choosing actions and its number of non-pass decisions. Search screens use three seeds and shortened horizons to identify promising conditions economically. Percentages can therefore move sharply with one game and must not be presented as precise population estimates.

## 1. Board designs

Figure 01 shows the default board and three strategic variants:

- `dual_arena`: two equal 2-point objectives separated by a blocked center;
- `open_7x7`: a larger open arena with a 2-point center and two 1-point side objectives;
- `bottleneck_7x7`: three passages across a blocked middle row, with a 3-point central passage.

Two additional 5×5 definitions change the piece count to two and four. All boards are symmetric between players, so move-order effects are not intentionally built into the geometry.

## 2. Robustness of the rule–greedy result

The baseline conclusion that `rule` dominates `greedy` is **environment-dependent**. On the default board, rule received 100% of win points across their 16 direct games. Greedy received 50% on the dual arena, 62% on the open 7×7 board, and 53% on the bottleneck board.

This reversal is substantively plausible. Rule’s fixed “capture, then objective” priority is well matched to a single recurring center. With several separated objectives, greedy’s full heuristic can trade off movement, threats, safety, and objective values more flexibly. The result justifies promoting board × agent interaction—not one global ranking—to a main report question.

Figure 02 covers the remaining factors. It should be read for large reversals only; eight seeds are insufficient for close conditions.

## 3. Deadlocks and deck composition

The capture-heavy deck is the clearest failure condition: 83% of its 48 games end with at least 10 consecutive passes, compared with 12% for the default-board control. Figure 03 confirms that card supply strongly affects whether the market enters an absorbing illegal state.

This supports a concrete design change before confirmatory testing: either discard/redraw one unavailable market card after a pass, refresh the market after both players pass, or terminate and score the game when the state is provably stuck. The original pass rule should remain as a labeled control.

### Selected rule and matched validation

The selected rule is now implemented as an optional mode parameter: **after two consecutive passes, discard the entire three-card market, deal three replacements, reset the counter, and continue**. Any legal action resets the counter immediately. Old modes omit the parameter and therefore replay with the original behavior.

In the matched capture-heavy fast screen, deadlocks fell from 83% to 0%, while draws fell from 33% to 0%. Figure 08 shows the corresponding default-deck control and the search-agent outcome comparison. Eliminating deadlocks increases actual decisions and therefore whole-game runtime; this is desired because the match is continuing rather than idling through passes.

## 4. Search agents across environments

Figures 04 and 05 compare `rule`, depth-2/top-6 `expectimax`, and MCTS with 100 simulations and rollout depth 10. Each agent has 12 observations per condition (two opponents, both orientations, three seeds).

The rankings change across boards and decks, while runtime changes with branching and pass frequency. In particular, four pieces substantially increase decision cost, and capture-heavy deadlocks make agents appear artificially fast because many scheduled turns require no decision. Runtime must therefore be reported per actual decision alongside pass rate—not only per match.

The three-seed results are useful for selecting confirmatory conditions, but they are too small to assert that one search agent is generally superior.

## 5. Expectimax depth

The best observed expectimax screen is depth 3 at 67% win points against rule. Depth 3 costs 13.7× as much per decision as depth 2 in this screen. With only six games per depth, the outcome curve is noisy; the reliable conclusion is computational: exact chance expansion becomes expensive very quickly even after limiting each decision node to the top four actions.

Recommended confirmatory comparison: depths 1–3, 30–50 paired seeds, fixed top-k, and both a fixed-depth and equal-time presentation.

## 6. MCTS budget

The strongest observed MCTS cell is 200 simulations with rollout depth 10, scoring 75% win points against rule. Figure 07 shows that simulations drive a near-linear cost increase, while greater rollout depth adds cost without a monotonic strength guarantee in this small sample.

Do not select the numerically highest cell and report it as proven optimal: nine cells were screened on only six games each. Instead, select two Pareto-efficient settings—one inexpensive and one high-budget—and rerun both with substantially more seeds.

## 7. Recommended confirmatory batch

Prioritize the following:

1. Default versus dual-arena versus open-7×7 boards, because the rule–greedy ranking reverses.
2. Default versus capture-heavy deck under both the original and revised pass rule.
3. Rule, greedy, expectimax depth 2, and two MCTS budgets; 50 paired seeds, both orientations.
4. Default three pieces versus four pieces, with per-decision runtime and legal-action counts.
5. Equal-time search comparisons after fixed-parameter results.

Use win points, score margin, time-to-goal, deadlock rate, scoring-source decomposition, adjacent/net capture counts, and milliseconds per actual decision. Treat seed as a paired block. Run both fixed-horizon and `score_to_win` modes because they answer different questions.

## 8. Spread spawns, objective values, and point-goal wins

Figure 09 introduces two symmetric spawn geometries. The 7x7 **inner ring** places each side on an opposing arc near the middle; the 9x9 **outer orbit** spreads the pieces farther around the objective. Each geometry has a concentrated objective, where holding the center is worth more than a capture (`capture_score = 1`), and a distributed-objective control.

The optional `score_to_win` rule now ends a match as soon as either score reaches its configured goal, while the turn limit remains a safety cap. All 192 fast-agent games ended decisively. The fastest condition was Inner ring / Single center, reaching its goal after 23.5 combined turns on average. Figure 10 and Table 11 report time-to-goal and agent outcomes. Because the inner and outer conditions use goals of 40 and 60 respectively, compare objective variants within a geometry, not raw turn counts across geometries.

## 9. Expectimax depths 2-6

A controlled single-decision benchmark took 1.166 s at depth 2, 10.274 s at depth 3, and 102.444 s at depth 4. Depth 5 exceeded the 120-second limit; depth 6 was skipped after that timeout. Even under a smaller top-2 action cap and a score goal of 20, the two depth-4 games averaged 126.1 seconds of measured decision time.

This establishes the feasible experimental boundary: use depths 2-3 for replicated full matches, depth 4 only as a tightly bounded computational demonstration, and do not spend the project budget on depths 5-6 without approximation, sampling, caching, or a strict time budget.

## 10. Net-launcher statistics

The game-log analysis now distinguishes adjacent captures from net launches by checking whether the capture move records a second source piece (the launcher). Across the 228 new spread-board fast/search games, agents made 1134 capture actions, of which 261 (23.0%) used the net. Figure 12 and Table 13 break this down by agent. Counts should be reported beside shares: an agent can have a high net share simply because it captures rarely.

## 11. Reproduction

All mode directories contain immutable board/deck snapshots, parameters, seeds, results, and per-turn games. Regenerate this package with:

```powershell
python analysis/future_experiments_report.py
```
