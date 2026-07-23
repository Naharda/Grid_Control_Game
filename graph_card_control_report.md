# Graph Card Control: Search-Based Agents for a Custom Stochastic Strategy Game

**Course:** 237-2-5513 Search Methods in Artificial Intelligence  
**Project idea:** Creating a search-based agent for a strategy game and comparing it against threshold agents such as random, rule-based, greedy, or human agents.  
**Code link:** TODO: add GitHub / submission repository link.  
**Authors:** TODO: add names and student IDs.

## Abstract

This project presents **Graph Card Control**, a custom two-player turn-based strategy game designed as a compact testbed for search-based game-playing agents. The game combines deterministic board movement, tactical captures, public card selection, and stochastic card replacement from a shared deck. The main research objective is to evaluate whether search-based decision making improves performance over simpler threshold agents in a new abstract game that is not a standard benchmark such as Chess, Checkers, Connect Four, or Backgammon.

We implemented the full game in Python, including legal action generation, state transitions, text and Pygame visualization, and several agents: random, rule-based, greedy heuristic, minimax, expectimax, and Monte Carlo Tree Search. Initial experiments show that a domain-specific rule-based baseline strongly outperforms random play, while the current greedy heuristic underperforms the rule-based agent. Expectimax performs well against random in a small sample, but deeper stochastic search is computationally expensive, motivating further work on action pruning, time limits, and larger-scale experiments.

## 1. Introduction and Literature Review

Game-playing has historically been one of the central domains for studying search in artificial intelligence. A game environment naturally defines states, actions, transition rules, terminal conditions, and utility values, making it possible to compare search algorithms in a controlled way. Classical adversarial search methods such as minimax and alpha-beta pruning are widely used for deterministic, perfect-information games. Russell and Norvig describe game-tree search as a standard model for agents that must choose actions while anticipating an opponent's responses [1].

However, many interesting games are not purely deterministic. They may include dice, card draws, hidden information, or random event generation. In such games, minimax must be extended with chance nodes, leading to expectiminimax or expectimax-style search, where decision nodes are combined with probability-weighted stochastic transitions [1]. This is relevant to Graph Card Control because all board positions and card decks are known, but after a card is used, a replacement card is drawn from the deck. The game is therefore a stochastic, perfect-information game.

Heuristic search is also relevant. A* search, introduced by Hart, Nilsson, and Raphael, formalized the use of heuristic estimates to guide search toward goal states efficiently [2]. Although A* is usually presented for single-agent pathfinding, tactical subgoals in games can often be framed as planning problems, such as reaching the center tile or forming a capture line. For this reason, the project includes A*, greedy best-first search, and bidirectional search as tactical planning modules rather than as the main adversarial decision procedures.

Monte Carlo Tree Search (MCTS) is another important approach for game-playing agents, especially when the branching factor is high or when exact tree expansion is too expensive. MCTS uses repeated simulations and an exploration-exploitation rule such as UCB1/UCT to estimate promising actions. Kocsis and Szepesvari introduced UCT as a bandit-based approach to Monte Carlo planning [3], and Browne et al. provide a broad survey of MCTS methods and applications in games [4]. Graph Card Control has a nontrivial branching factor because card effects such as Mobilize and Swap generate many legal actions, making MCTS a natural candidate.

The contribution of this project is not a new search algorithm, but a new experimental domain and implementation for comparing search-based agents against meaningful baselines. The game was intentionally designed to include several strategic incentives: center control rewards fast positional play, capture scoring rewards tactical formations, and swap actions prevent stable formations from becoming too dominant. This gives the agents a meaningful tradeoff between immediate scoring, tactical threats, and long-term positioning.

## 2. Methodology

### 2.1 Game Definition

Graph Card Control is a two-player, turn-based abstract strategy game played on a 5x5 grid represented internally as a graph. Each player controls three pieces. Player A starts at the top of the board and Player B starts at the bottom:

- Player A: `(0,1), (0,2), (0,3)`
- Player B: `(4,1), (4,2), (4,3)`

The center tile is `(2,2)`. A player receives:

- `+1` point for occupying the center at the end of their turn.
- `+3` points for a successful capture.

The game lasts 50 turns per player. The winner is the player with the higher score after both players finish all turns.

### 2.2 Cards and Stochasticity

The game uses a shared deck and a public market of three visible cards. On each turn, the current player selects one visible card, applies it, discards it, and draws a replacement from the deck. If the deck is empty, the discard pile is shuffled into a new deck.

The implemented cards are:

| Card | Effect |
|---|---|
| Move 1 | Move one friendly piece up to one orthogonal tile. |
| Move 2 | Move one friendly piece up to two orthogonal tiles. |
| Mobilize | Move two different friendly pieces up to one tile each. |
| Capture / Net Launcher | Capture adjacent enemy, or use an orthogonally adjacent friendly pair to capture along their shared line. |
| Swap | Swap one friendly piece with one enemy piece within Manhattan range 3. |

The default deck composition is:

| Card | Count |
|---|---:|
| Move 1 | 8 |
| Move 2 | 6 |
| Mobilize | 5 |
| Capture | 5 |
| Swap | 4 |

### 2.3 Implementation

The implementation is written in Python. The code is organized into modules:

| Module | Purpose |
|---|---|
| `src/game` | Board, cards, actions, state representation, rules, and engine. |
| `src/agents` | Random, rule-based, greedy, human, search, and MCTS agents. |
| `src/search` | Heuristic evaluation, minimax, expectimax, MCTS, A*, greedy best-first, and bidirectional helpers. |
| `src/visualization` | Text renderer and interactive Pygame visual game/review tool. |
| `src/experiments` | Single-match runner, game-mode creation/execution/reconstruction, and result analysis. |
| `tests` | Smoke tests for the core game. |

The most important implementation decision is that all agents use the same legal action generator:

```python
get_legal_actions(state) -> list[Action]
```

and the same transition function:

```python
apply_action(state, action) -> GameState
```

This ensures that random, rule-based, greedy, minimax, expectimax, MCTS, and human play all operate over the same game model.

### 2.4 Agents

The following agents were implemented:

| Agent | Description |
|---|---|
| Random | Chooses uniformly from legal actions. |
| Rule-based | Captures whenever possible; otherwise prioritizes center occupation or movement toward the center. |
| Greedy | Evaluates all immediate successor states using the heuristic and chooses the best one. |
| Minimax | Depth-limited deterministic adversarial search with alpha-beta pruning. |
| Expectimax | Depth-limited adversarial search with chance-node expectation over card replacement. |
| MCTS | Monte Carlo Tree Search using UCB-style child selection and random rollouts. |
| Human | Text or Pygame-driven human interaction. |

The search agents ship with explicit defaults: minimax and expectimax use `depth=2` with `top_k=10` beam filtering, and MCTS uses `simulations=200` with `rollout_depth=20`. The depth limit and top-K action filtering (keeping only the K best immediate successors by heuristic score) are the primary controls on the game's branching factor; alpha-beta pruning applies only to the deterministic minimax variant, while expectimax expands chance nodes exactly over the replacement-card draw distribution. These hyperparameters are recorded verbatim into each game mode's config, so every experiment snapshot documents the exact agent settings it was run with.

### 2.5 Heuristic Function

The heuristic evaluates a state from one player's perspective:

```text
H(state, player) =
  100 * score_difference
+ 10  * center_control
+ 2   * center_distance_advantage
+ 15  * capture_threats
+ 20  * net_launcher_potential
+ 8   * swap_potential
+ 10  * piece_safety
+ 1   * mobility
```

The score term is intentionally dominant because the game objective is score maximization. The other terms estimate positional strength, tactical opportunities, safety, and future action availability:

| Component | Meaning |
|---|---|
| `score_difference` | `my_score - opponent_score`; the dominant term. |
| `center_control` | Occupying the scoring cell(s). |
| `center_distance_advantage` | Sum of opponent piece distances to the nearest scoring cell minus own. |
| `capture_threats` | Enemies capturable next move: adjacent enemies plus enemies hittable by a Net Launcher ray. |
| `net_launcher_potential` | Friendly orthogonally adjacent pairs with an enemy on their line, and near-pairs. |
| `swap_potential` | Useful swaps in range: displacing an enemy from a scoring cell or breaking a formation. |
| `piece_safety` | Penalty for exposure: pieces adjacent to an enemy, on an enemy net line, or vulnerable to swap-then-capture. |
| `mobility` | Legal action count; deliberately weighted low so it cannot dominate. |

The weights live in `GameConfig.heuristic_weights` and are recorded into each mode config, so they are tunable per experiment. On custom boards the `center`/`center_distance` components generalize to weighted **capture cells** (control of, and distance to, the nearest scoring cell); the default board has the single 1-point center.

### 2.6 Evaluation Method

Experiments are packaged as **game modes**: a mode is a pre-declared, self-contained bundle under `modes/<name>/` whose `config.json` embeds full board and deck snapshots, all rule values, the heuristic weights, every agent's exact hyperparameters, the per-game seeds, and the agent seed policy. A mode is therefore reproducible on its own even if the shared board/deck files change later.

Running a mode plays **every ordered pair** of its agents — including mirrored orderings and self-play — with the same seeds in both orientations, so first-move advantage can be measured directly. Each pair produces a results CSV (`modes/<name>/results/<a>_<b>.csv` with winner and final scores per game) plus a per-turn move log for every game (`modes/<name>/games/<a>_<b>/<i>.csv`), which can be replayed and validated move-by-move with `reconstruct_game.py`.

The main command format is:

```bash
python src/experiments/create_mode.py baseline --agents greedy random --games 20
python src/experiments/run_mode.py baseline
python src/experiments/analyze_results.py modes/baseline/results/greedy_random.csv
```

The current experiments are preliminary smoke-scale experiments, intended to validate the system and expose early behavioral patterns. Larger experiments should be run before final submission.

## 3. Experimental Results

### 3.1 Environment

Experiments were run in a Conda environment using Python 3.13. The full test suite passed:

```text
66 passed in 0.51s
```

### 3.2 Preliminary Results

These preliminary results were produced with an earlier single-pair runner that predates the game-mode system; final experiments will be re-run as modes.

| Matchup | Games | Player A Wins | Player B Wins | Draws | Avg. A-B Score Difference |
|---|---:|---:|---:|---:|---:|
| Rule-based vs Random | 30 | 29 | 0 | 1 | +98.00 |
| Greedy vs Rule-based | 30 | 0 | 28 | 2 | -35.43 |
| Expectimax vs Random | 5 | 3 | 0 | 2 | +61.20 |

### 3.3 Analysis

The rule-based agent strongly outperformed random play, winning 29 of 30 games with an average score difference of +98. This shows that Graph Card Control rewards coherent strategy and is not dominated by random card draws. A simple policy of capturing when possible and otherwise moving toward the center is already much stronger than random action selection.

The greedy heuristic agent lost heavily to the rule-based agent. This is an important result because it suggests that the current heuristic, although richer than the rule-based policy, may not be calibrated correctly. The greedy agent maximizes a weighted evaluation of the immediate successor state, but the rule-based agent follows a sharper tactical priority: capture first, center second. The result indicates that the heuristic may overvalue secondary terms such as mobility, swap potential, or net potential relative to directly useful tactical objectives.

Expectimax beat random in the small 5-game sample, winning 3 games and drawing 2. However, expectimax is much slower than rule-based or greedy play because it evaluates action choices, opponent responses, and stochastic card draws. A 20-game expectimax series exceeded the quick-run time budget, which demonstrates the practical importance of top-K pruning, depth limits, and possibly time-limited search.

MCTS was implemented, but the default setting of 200 simulations per move was too slow for quick experiment-scale evaluation in the current environment. This does not invalidate MCTS as a project component; rather, it suggests that the final experimental design should include a configurable simulation budget such as 25, 50, 100, and 200 rollouts per move, and should measure both win rate and decision time.

## 4. Experimental Conclusions and Summary

The project objective was to create a custom strategy game and compare search-based agents against threshold agents. This objective was achieved at the implementation level: the game, agents, search algorithms, visualization, game-mode experiment runner, and analysis scripts are all implemented and runnable.

The initial results support several conclusions:

1. Graph Card Control is strategically meaningful: a simple rule-based strategy strongly beats random play.
2. A hand-designed heuristic is not automatically superior to a simple tactical policy; the greedy agent requires further tuning.
3. Search-based agents such as expectimax are promising but computationally expensive due to stochastic card replacement and branching-factor growth.
4. The game is suitable for further research because it exposes tradeoffs between tactical captures, center control, card availability, and computational cost.

The main limitation of the current work is that the experiments are still preliminary. The sample sizes are small, and the slower agents need better runtime controls before large experiments can be completed. In addition, the current report includes tables but not yet generated plots.

Recommended remaining implementation work before final submission:

- Add timing metrics per move and nodes expanded per decision.
- Add plot generation from CSV results.
- Run larger experiments, for example 100 games per matchup.
- Tune or ablate the heuristic weights to explain why greedy loses to the rule-based baseline.
- Include MCTS results at several rollout budgets.
- Test deck-composition variants as modes, e.g. a rush deck (Move1: 6, Move2: 10, Mobilize: 8, Capture: 3, Swap: 3) and a combat/formations deck (Move1: 6, Move2: 4, Mobilize: 5, Capture: 9, Swap: 6) against the default balanced deck.

## 5. Reproducibility

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Run tests:

```bash
python -m pytest
```

Play the game in the Pygame GUI:

```bash
python start_game.py --gui --a human --b greedy
```

Define and run a game mode (all non-human agents, every ordered pair, fixed seeds):

```bash
python src/experiments/create_mode.py full --all-agents --games 20
python src/experiments/run_mode.py full
```

Analyze results and replay a recorded game to validate it:

```bash
python src/experiments/analyze_results.py modes/full/results/greedy_random.csv
python src/experiments/reconstruct_game.py full greedy random 0 --gui
```

## References

[1] Stuart Russell and Peter Norvig. *Artificial Intelligence: A Modern Approach*, 4th edition. Pearson, 2020. See also: http://aima.cs.berkeley.edu/

[2] Peter E. Hart, Nils J. Nilsson, and Bertram Raphael. "A Formal Basis for the Heuristic Determination of Minimum Cost Paths." *IEEE Transactions on Systems Science and Cybernetics*, 1968.

[3] Levente Kocsis and Csaba Szepesvari. "Bandit Based Monte-Carlo Planning." *European Conference on Machine Learning*, 2006.

[4] Cameron B. Browne, Edward Powley, Daniel Whitehouse, Simon M. Lucas, Peter I. Cowling, Philipp Rohlfshagen, Stephen Tavener, Diego Perez, Spyridon Samothrakis, and Simon Colton. "A Survey of Monte Carlo Tree Search Methods." *IEEE Transactions on Computational Intelligence and AI in Games*, 2012.

[5] Donald E. Knuth and Ronald W. Moore. "An Analysis of Alpha-Beta Pruning." *Artificial Intelligence*, 1975.
