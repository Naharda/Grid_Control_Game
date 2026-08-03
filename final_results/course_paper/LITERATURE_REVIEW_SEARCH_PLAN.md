# Literature-review reading and search plan

This is a reading guide, not a request to add citations mechanically. For each source, extract: (1) the relevant method or result, (2) the assumption that matters here, and (3) the precise relationship to Graph Card Control. The manuscript should compare approaches, not present a chronological list.

## Core sources already integrated

| Topic | Primary source | What to verify while reading | How it supports the paper |
|---|---|---|---|
| Chance-node search | Ballard, “The *-Minimax Search Procedure for Trees Containing Chance Nodes” (1983), [DOI](https://doi.org/10.1016/S0004-3702(83)80015-0) | Chance nodes back up probability-weighted values; pruning requires valid value bounds | Establishes why ordinary deterministic minimax is not the correct model and motivates exact expectimax/*-minimax |
| UCT | Kocsis and Szepesvári, “Bandit Based Monte-Carlo Planning” (2006), [paper](https://people.eecs.berkeley.edu/~russell/classes/cs294/s11/readings/Kocsis%2BSzepesvari%3A2006.pdf) | Exploration–exploitation rule and the difference between asymptotic consistency and fixed-budget behavior | Frames the 100-simulation MCTS as a bounded implementation, not a universal statement about MCTS |
| Early MCTS backups | Coulom, “Efficient Selectivity and Backup Operators in Monte-Carlo Tree Search” (2006), [author page](https://www.remi-coulom.fr/CG2006/) | How sampling allocates effort selectively and how simulation values are backed up | Contrasts sampling-based allocation with exhaustive chance expansion |
| Sparse stochastic planning | Kearns, Mansour, and Ng, “A Sparse Sampling Algorithm for Near-Optimal Planning in Large Markov Decision Processes” (1999), [IJCAI paper](https://www.ijcai.org/Proceedings/99-2/Papers/093.pdf) | A generative model can replace exhaustive stochastic branching, but cost remains exponential in horizon | Provides the conceptual basis for sampling public refill outcomes in MCTS |
| Stochastic adversarial MCTS | Lanctot et al., “Monte Carlo *-Minimax Search” (2013), [IJCAI paper](https://www.ijcai.org/papers13/Papers/IJCAI13-093.pdf) | How stochastic outcomes, opposing choices, and sampling are combined; note its equal-time comparisons | Closest algorithmic comparator to the corrected adversarial stochastic MCTS |
| Depth pathology | Pearl, “On the Nature of Pathology in Game Searching” (1983), [DOI](https://doi.org/10.1016/0004-3702(83)90004-8) | Conditions under which minimax backups amplify evaluation error | Supports a cautious interpretation of non-monotonic depth results; it does not prove pathology here |
| General game playing | Genesereth, Love, and Pell, “General Game Playing: Overview of the AAAI Competition” (2005), [paper](https://logic.stanford.edu/ggp/readings/aaai.pdf) | Motivation for formal, unfamiliar game domains and solver-independent evaluation | Positions the configurable game itself as part of the project’s contribution |

## Highest-value complementary reading

1. **MCTS survey and stochastic variants.** Read Browne et al., “A Survey of Monte Carlo Tree Search Methods” (2012), [paper](https://www.lamsade.dauphine.fr/~cazenave/A%2BSurvey%2Bof%2BMonte%2BCarlo%2BTree%2BSearch%2BMethods.pdf). Search within it for *stochastic games*, *chance nodes*, *open loop*, and *backup*. Use it to check whether our terminology for sampled chance edges and adversarial backup matches standard usage.

2. **Experimental fairness at equal compute.** Follow the evaluation design in Lanctot et al. and search for `MCTS expectimax equal thinking time stochastic games`. Extract which budget is held fixed—wall-clock time, node expansions, or simulations. This is the most important future experiment because our current comparison fixes algorithm-specific hyperparameters rather than equal time.

3. **Heuristic knowledge in MCTS.** Search for `knowledge guided MCTS rollout policy board games` and start with Gelly and Silver, “Combining Online and Offline Knowledge in UCT” (2007). Use it to design an ablation separating the contribution of the shared heuristic from the tree-search procedure.

4. **Depth sensitivity.** Search for `minimax pathology heuristic correlation empirical game search` and read Nau, “An Investigation of the Causes of Pathology in Games” (1982), DOI 10.1016/0004-3702(82)90002-9. Only use the word *pathology* if the proposed conditions are tested; the present evidence establishes only that deeper expectimax was not uniformly stronger.

5. **Paired simulation design.** Search for `common random numbers paired simulation experiments` and read Heikes, Montgomery, and Rardin, “Using Common Random Numbers in Simulation Experiments” (1976), DOI 10.1177/003754977602700301. This can justify mirrored seeds and guide a future paired interval or hierarchical analysis.

## Questions the literature review should answer

- Why do exact chance expansion and stochastic sampling represent different cost–accuracy trade-offs?
- Why must a two-player tree alternate maximizing and minimizing choices even when chance outcomes are sampled?
- What does a fixed simulation or depth budget permit us to conclude—and what would require an equal-time curve?
- Why can a compact rule policy outperform generic bounded search without implying that search is generally inferior?
- Which claims are properties of the implemented agents, and which are established results from the literature?

## Assaf-style writing rule

For every cited paper, use at most three functional sentences: its relevant result, the assumption or limitation, and the comparison to this project. Avoid authority phrases (“it is well known”), unsupported mechanisms, and citations that do not change the argument.
