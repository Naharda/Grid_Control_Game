# Corrected-agent rerun record

## Correction implemented

The submitted analysis uses agents that condition only on public information. Greedy and rule-based successor evaluation marginalize over the public remaining-card distribution. Expectimax retains exact chance expansion and orders its bounded beam from the acting player's perspective. MCTS samples refills from public counts with an agent-local random generator and treats opponent nodes adversarially. Hidden-deck reversal tests found no changed choice at the audited checkpoints for greedy, rule, expectimax depth 2, or MCTS.

## Executed design

- Main reduced-factorial study: six agents, both move orders, three boards, and fixed-horizon, 10-point, and 40-point stopping rules.
- Independent deck study: default, movement-heavy, capture-heavy, and swap-heavy decks on the default board under the fixed horizon.
- Depth-feasibility study: expectimax depths 4–6 under a deliberately bounded set of games; the primary depth comparison uses matched depth-2 and depth-3 games from the main study.
- Three game seeds were used for the main and deck cells. The explicitly bounded depth study uses fewer replications where computation made the full design infeasible; the paper labels this evidence separately.

The resulting archive contains 15 corrected modes, 396 ordered non-self pair files, and 1,116 games. Every result row has a corresponding game log, and all 1,116 logs replay to the recorded outcome.

## Execution and integrity notes

The sequential main rerun took approximately 2.82 hours on the recorded machine. One bottleneck/goal-10 mode overlapped a dependency-install process, so the entire intended mode was rerun sequentially. The generic runner also emitted six unintended self-play pairs for that mode; those result files and their matching log directories were identified and removed. The final validated mode contains only the 30 intended ordered non-self pairs.

Legacy modes were not overwritten. They are retained only for the hidden-information implementation audit; every quantitative result in the final paper comes from modes whose names begin with `corrected_`.

## Validation outcome

- Unit and regression tests: 78 passed.
- Coverage: 1,116/1,116 expected corrected games present.
- Replay validation: 1,116/1,116 corrected logs reproduced their recorded outcomes.
- Artifact validation: 15 modes, 19 sorted table exports, seven raster/vector figure pairs, and seven nonblank paper pages.
