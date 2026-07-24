# Baseline Full: analysis and interpretation

## Executive summary

This package analyzes all **1,080 games** in `modes/baseline_full`: 36 ordered pairings, 30 seeded games per pairing, with 100 scheduled turns per game. Competitive rankings exclude self-play, leaving 300 observations per agent (150 first-player and 150 second-player games). Draws count as half a win in the main “win points” measure.

The strongest aggregate performer is **rule** with 79.8% win points and a mean score margin of 25.96; **minimax** is next at 69.7%. These estimates describe this board, deck, heuristic, and parameter budget—not universal agent strength.

Move order matters: across all non-self matchups, Player A receives 53.7% of win points. Agent-specific first/second results are in Figure 02 and the paired-seed differences in Table 03. Pairing the same agent/opponent/seed across reversed orientations is the cleanest available estimate because it controls the shuffled deck seed.

A major experimental finding is the frequency of **absorbing market deadlocks**. In 19.6% of games, the final 10 or more scheduled turns are all passes; 16.1% of all scheduled turns are passes. The rules leave the market unchanged on a pass, so a market containing only currently illegal cards can remain stuck forever. This is not merely cosmetic: it truncates strategic interaction and can preserve an early lead. Report this prominently and test a pass/redraw rule as a robustness condition.

## 1. What the project studies

Graph Card Control is a two-player, alternating, perfect-information strategy game with stochastic card refills. Each player controls three pieces on a 5×5 grid. The default match lasts 50 turns per player. Captures score 3 points, while occupying the center scoring cell yields 1 point after every own turn. Players choose from a shared three-card market containing movement, mobilization, capture, and swap actions. The only hidden uncertainty is the next card drawn; the remaining card-type distribution is known.

The experiment compares two baselines (`random`, `rule`) with four evaluation/search agents (`greedy`, depth-2 `minimax`, depth-2 `expectimax`, and `mcts` with 200 simulations and rollout depth 20). The current minimax implementation does **not** create chance nodes: its ordinary transition call consumes the next concrete card from the shuffled deck stored in `GameState`, so its search follows the realized hidden deck order deterministically. Expectimax instead enumerates possible replacement card types and probability-weights their successor values; MCTS estimates longer-run values through sampled simulations.

## 2. Performance and move order

Figure 01 gives both win points and score margin. Figure 03 is essential context: aggregate rankings can hide rock–paper–scissors matchup structure. Each off-diagonal head-to-head cell pools 30 games in each orientation (60 total).

The first/second comparison should be interpreted in two layers:

1. **Overall game bias:** Player A obtains 53.7% of competitive win points.
2. **Agent sensitivity:** compare each agent’s random: 10.3% first vs 2.3% second, rule: 84.3% first vs 75.3% second, greedy: 31.0% first vs 25.0% second, minimax: 72.7% first vs 66.7% second, expectimax: 71.0% first vs 64.7% second, mcts: 53.0% first vs 43.7% second.

Table 03 reports paired first-minus-second differences over identical opponent/seed combinations, including bootstrap 95% intervals. A confidence interval spanning zero means the current 30-seed-per-orientation sample does not clearly establish a seat effect for that agent.

## 3. Runtime versus playing strength

The original CSV files do **not** record elapsed time. Figure 04 therefore uses a post-hoc benchmark: every agent chooses an action from the same six reconstructed early/middle/late recorded states. Values are median wall-clock milliseconds per decision on this machine, not whole-match runtimes. Fast agents are repeated within each state to reduce timer noise; search-heavy agents run fewer repetitions.

The slowest median decision time is **expectimax** at 1158.168 ms. Among heuristic/search agents, the cheapest measured option is **greedy** at 10.725 ms. The performance–cost plot supports an explicit efficiency argument: prefer an agent on the upper-left frontier, and describe any extra win rate in terms of its multiplicative runtime cost. Do not mix these post-hoc timings with the original outcome sample as if they were collected simultaneously.

## 4. Dominant strategies

“Strategy” is operationalized using three observable quantities:

- selected card type on non-pass turns (Figure 05);
- scoring source—3 points per logged capture versus residual scoring-cell control points (Figure 06);
- capture style—melee versus net launcher, identified by the second launcher source field (Table 09).

**rule** earns the most scoring-cell control points (30.77 per game), while **greedy** makes the most captures (9.99 per game). The contrast between `rule` and `greedy` is particularly informative: they average 9.58 and 9.99 captures, respectively, but `rule` earns 30.77 control points versus only 11.33 for `greedy`. The dominant pattern is therefore not capture volume alone; it is opportunistic capture combined with persistent scoring-cell control.

These are behavioral signatures, not causal effects: card availability, legality, opponent behavior, and deadlocks all constrain what an agent can choose. Table 08 therefore includes a descriptive `chosen_per_exposure_turn` measure alongside raw choice share; exposure means the card appeared in the market, not that at least one action using it was legal.

Figure 07 shows when scores accumulate. Plateaus near the end of a match should be read together with Figure 08: many are caused by pass streaks, not stable defensive equilibrium.

## 5. Threats to validity

- **One environment:** the ranking is conditional on the default symmetric 5×5 board, one 1-point center, three pieces each, and the default 28-card deck.
- **One heuristic:** greedy, minimax, expectimax, and MCTS rollouts share the same evaluation weights, so their errors are correlated.
- **Minimax has hidden-order information:** minimax calls `apply_action` without a forced draw, causing search to use the next concrete card in the state’s shuffled deck. Under the written rules only deck composition—not order—is public. Its strong result may therefore be inflated by oracle-like future-card information and should be rerun after correcting the chance model.
- **Budget mismatch:** depth 2, top-k 10, and 200 MCTS simulations are not guaranteed to represent equal computation.
- **Seed dependence:** 30 seeds per orientation is useful but still finite. Reversed orientations reuse seeds, which is good for paired seat analysis but means observations are not all independent.
- **Deadlocks:** end-of-game pass streaks reduce the effective horizon and may reward early scoring disproportionately.
- **Timing provenance:** runtime is post-hoc and machine-specific because it was absent from the original logs.

## 6. Recommended follow-up experiments

Use a factorial design where one factor changes at a time from the baseline, retain mirrored orientations, and increase to at least 50–100 seeds for close comparisons. Record per-decision elapsed time, expanded nodes/simulations, pass status, and terminal deadlock length directly during the run.

1. **Boards:** test the existing `crossfire` board plus small/large and multi-scoring-cell layouts. Hypothesis: longer distances favor deeper planning; multiple weighted cells reduce center congestion and may reduce deadlocks.
2. **Pieces per player:** compare 2, 3, and 4 pieces on boards sized to avoid spawn congestion. Hypothesis: more pieces increase branching, net opportunities, blocking, and MCTS’s sampling burden.
3. **Deck composition:** create movement-heavy, capture-heavy, swap-heavy, and balanced decks while keeping deck size fixed. Include a robustness variant that redraws or refreshes the market after a pass. Hypothesis: capture-heavy markets increase absorbing illegal-card states under the current rule.
4. **Win condition / scoring:** the implemented game uses a fixed horizon and highest score, not a point threshold. Test horizons (25/50/75 turns per player), capture values (1/3/5), scoring-cell weights, and—only as a separate rule variant—first-to-target thresholds. Threshold games confound performance with variable runtime, so analyze both win rate and turns-to-finish.
5. **Expectimax depth:** depths 1, 2, and 3 (possibly 4 if feasible), holding `top_k=10`, with time/node budgets recorded.
6. **MCTS budget:** a grid over simulations {50, 100, 200, 500, 1000} and rollout depths {5, 10, 20, 40}. Plot win points against wall time to find diminishing returns.
7. **Fair-budget comparison:** cap all search agents by equal milliseconds per move in addition to parameter sweeps. This answers whether an algorithm is better, not merely allowed more computation.
8. **Ablations:** remove heuristic terms one at a time, especially scoring-cell distance, capture threat, and net potential, to explain which knowledge drives performance.

For each follow-up, pre-register the primary metric (competitive win points), secondary metrics (score margin, control/capture scoring split, deadlocks), and the paired-seed seat contrast. Avoid selecting only favorable configurations after seeing results.

## 7. Reproducibility

Run:

```powershell
python analysis/baseline_full_report.py
```

The script reads raw data without modifying it, validates each log’s final score against its result CSV, regenerates all tables/figures, uses a fixed bootstrap seed, and rewrites this analysis and the index. The mode snapshot records code version `78546b4` and seeds 0–29.
