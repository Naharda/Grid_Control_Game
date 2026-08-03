# Assaf-style content audit

This audit applies concise, evidence-led, claim-calibrated writing principles to the paper without importing rebuttal structure.

| Severity | Obligation | Finding | Repair | Verification |
|---|---|---|---|---|
| Critical | Agent semantics | Legacy simulated successors could consume the stored next refill; legacy MCTS also maximized root value at opponent nodes. | Added public-information successor helpers, stochastic MCTS action edges, adversarial opponent selection, and direction-correct expectimax beam ordering; reran under new mode names. | Hidden-deck audit reports zero sensitive checkpoints; semantic unit tests and complete replay validation pass. |
| Major | Claim scope | Algorithm-family claims would exceed a comparison of fixed budgets and one shared heuristic. | Every strength statement is framed as applying to the evaluated implementation and budget. | Abstract, Results, and Conclusions explicitly reject universal rankings. |
| Major | Causality | Strategy descriptions can be mistaken for explanations of win rate. | Dominant-strategy prose distinguishes recorded behavior from mechanism and calls for heuristic ablation. | Net-launcher counts are not presented as causal evidence of winning. |
| Major | Runtime | Timing without execution context is difficult to interpret. | Recorded CPU, operating system, Python version, sequential policy, and timer denominator. | `RUNTIME_ENVIRONMENT.md` and Methodology agree. |
| Major | Denominators | Board, deck, direct-depth, bounded-depth, and capture analyses use different cohorts. | Every figure legend states games or agent-game observations, scoring unit, and exclusions. | Legends are generated with data-dependent capture counts and checked against source tables. |
| Major | Literature | A citation list alone would not satisfy the course requirement. | Organized the review around exact chance backup, sparse sampling, UCT/MCTS, heuristic depth effects, and unfamiliar game domains; each source is connected to a design choice. | All bibliography entries are cited in the text; complementary reading is separated into a search plan. |
| Minor | Metadata | The prior draft used an anonymous placeholder. | Added both names and student IDs to the title block and PDF metadata. | Omri Avital (208693341); Itai Reder (318850781). |
| Minor | Reproducibility | Summary tables alone do not expose all observations. | Added sorted exports for all 1,116 game rows, all agent-game rows, coverage, order, depth, and capture events. | `tables/15_all_1116_game_results.csv` is the single complete game-level table. |

Final visual checks are recorded separately in `FIGURE_LAYOUT_AUDIT.md`; quantitative claims are mapped to files in `EVIDENCE_LEDGER.csv`.
