# Reduced factorial experiment report

## Design and coverage

The completed suite contains **1,116 games**:

- 810 games crossing three boards (default, bottleneck 7x7, inner-ring center) with fixed 25-turn, first-to-10, and first-to-40 end conditions;
- 270 independent deck games on the default board (movement-heavy, capture-heavy, swap-heavy; the default-deck control is shared with the board suite);
- 36 bounded first-to-20 games directly comparing rule and expectimax depths 2, 3, and 4.

Every main/deck condition contains six agents, all 30 ordered non-self pairs, three matched seeds, and the two-consecutive-pass market refresh. The coverage manifest verifies all result rows and per-game logs. Depths 2 and 3 use the same top-2 action cap and play each other directly. Depth 4 is bounded to one seed; depths 5-6 remain computationally infeasible.

## Main performance

Across the 12 unique main/deck modes, **Rule** has the highest aggregate win-points rate (69.0%). Figure 01 shows that rankings depend on board and end condition; Figure 03 isolates deck composition.

These are screening estimates: each agent has 30 games per condition, but each direct matchup has only six games. Interpret large reversals, not small percentage differences.

## Agent order

All matchups use identical seeds in both orientations. The largest aggregate first-seat advantage is for **Expectimax d3** at +7.5% win points; the smallest (or most negative) is **MCTS** at -1.9%. Figure 02 and Table 03 provide every agent's first/second split.

## Boards and point goal

The first-to-10 condition ended after 12.1 combined turns on average across boards; first-to-40 ended after 38.5, versus 50.0 scheduled turns under the 25-turn-per-player condition. This changes both strategy and compute cost, so goal-based and fixed-horizon results should be reported separately rather than pooled as interchangeable replications.

The inner-ring single-center board is the concentrated-objective condition: its +4 center reward exceeds the default +3 capture reward, making rushing and holding the center locally more valuable than one capture.

## Deck composition

Deck composition is tested independently on the default board with a fixed 25-turn horizon. This avoids confusing deck effects with board geometry or early stopping. All deck modes use the refreshed market, so the earlier absorbing capture-heavy market no longer contaminates the comparison.

## Expectimax depth

Across the six board/end direct comparisons, depth 3 receives 48.1% of win points against depth 2 over 54 agent-game observations. The result varies by condition and is not monotonic evidence that deeper is always stronger.

The bounded depth study shows the computational jump through depth 4 on all three boards. Depth 4 has only six games per board across three opponents and should be treated as timing/feasibility evidence, not a stable strength estimate.

## Net launcher

Across the full completed suite, 1715 of 8041 captures (21.3%) use the net launcher. Figure 06 and Table 07 report both counts and shares by agent. Counts matter alongside percentages because agents differ substantially in total capture frequency.

## Reproduction

```powershell
python analysis/reduced_factorial_report.py
```
