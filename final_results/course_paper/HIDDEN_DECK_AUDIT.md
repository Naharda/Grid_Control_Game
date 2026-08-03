# Hidden-deck invariance audit

## Question

Can an agent's selected action change when the board, public market, scores, remaining deck multiset, and agent seed are fixed, but the stored order of the hidden deck is reversed or permuted?

## Legacy diagnostic

Twelve reachable checkpoints from `reduced_board_default_fixed_r2` were evaluated under 12 deck-order permutations (eight checkpoints for MCTS). The legacy implementation changed its choice at 1/12 greedy checkpoints, 2/12 expectimax-depth-2 checkpoints, and 6/8 MCTS checkpoints; rule changed at 0/12. The diagnostic established an interface defect: unforced simulated successors could consume the actual next match refill.

Source table: `tables/18_hidden_deck_sensitivity_legacy.csv`.

## Corrected implementation

The correction preserves the ordered deck for deterministic match execution and replay but removes it from agent-side successor reasoning:

- greedy and rule ordering use a deterministic most-probable draw computed from public card counts;
- expectimax orders its top-2 beam from public-information successors and expands the exact refill distribution;
- MCTS samples refill cards from public counts with an agent-local random generator and keys outcome nodes by public state;
- expectimax beam ordering and MCTS selection minimize at opponent nodes.

The same fixed-public-state audit was repeated after correction.

| Agent | Checkpoints | Sensitive checkpoints | Mean unique actions |
|---|---:|---:|---:|
| Greedy | 12 | 0 | 1.000 |
| Rule | 12 | 0 | 1.000 |
| Expectimax depth 2 | 12 | 0 | 1.000 |
| MCTS | 8 | 0 | 1.000 |

Source table: `tables/19_hidden_deck_sensitivity_corrected.csv`. Unit tests in `tests/test_public_search.py` independently reverse the hidden deck and assert choice invariance.

## Interpretation

The corrected audit is an implementation invariant, not a performance result. It shows that tested decisions no longer condition on the stored hidden ordering. It does not establish statistical stability across random seeds, nor does it make a fixed simulation or beam budget equivalent to an exact solver.
