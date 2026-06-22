# Graph Card Control Game — Codex Implementation Plan

## 0. Project Context

This project is for a Search Methods in Artificial Intelligence final project. The goal is to build a small stochastic, perfect-information, turn-based abstract game, then compare different agents and search strategies on it.

The game should be original enough to avoid being a known benchmark, while still being simple and structured enough for systematic experiments.

Working title:

**Graph Card Control**

---

## 1. Game Objective and Core Mechanics

### Game Type

- Two-player, turn-based game.
- Perfect information: all board positions, scores, visible cards, and deck composition are known to both players.
- Stochasticity comes from the random replacement of used cards from the deck.
- The game is played for a fixed number of turns.

### Players and Pieces

- Each player has **3 identical pieces**.
- Pieces start at predefined spawn positions.
- Pieces are not permanently eliminated.
- When a piece is captured, it immediately returns to its owner's spawn area.

### Game Length

- The game lasts **50 turns per player**.
- One full round means each player has taken one turn.
- After both players complete 50 turns, the player with the higher score wins.

### Scoring

The score should combine both rushing and formation/combat strategies.

Initial scoring proposal:

- **+1 point** for controlling or occupying the center.
- **+3 points** for each successful capture.

This is intentionally asymmetric:
- Center scoring rewards early/rush strategies.
- Capture scoring rewards formation-based tactical play.

The exact values should be configurable.

### Center Control

For the first implementation, use a single center tile.

Recommended initial rule:

- A player gets **+1 point at the end of their turn** if one of their pieces occupies the center tile.

Alternative later rule:
- Score center only if the player controls the center region.
- Score center using majority of adjacent pieces.
- Score center at checkpoints instead of every turn.

Do not implement alternatives yet unless explicitly requested.

---

## 2. Cards Participating in the Game

The game uses a shared deck. A fixed number of cards are face-up in a public market.

### Public Market

- At any time, **3 cards** are visible.
- On a turn, the current player chooses one visible card and applies its effect.
- After the card is used, it is replaced by drawing a new card from the deck.
- If the deck is empty, reshuffle the discard pile into a new deck.
- The deck composition should be known to the agent.

### Card Types

Implement the following 5 card types.

---

### 2.1 Move 1

**Effect:**

Move one friendly piece by exactly or up to 1 tile.

Recommended implementation:

- Allow moving up to 1 tile.
- Legal movement is orthogonal on the grid: up, down, left, right.
- Cannot move through occupied tiles.
- Cannot end on occupied tiles unless future rules explicitly allow it.

No formation enhancement.

---

### 2.2 Move 2

**Effect:**

Move one friendly piece by up to 2 tiles.

Recommended implementation:

- Movement uses grid paths.
- The piece may move 1 or 2 orthogonal steps.
- Cannot pass through occupied tiles.
- Cannot end on occupied tiles.

No formation enhancement.

---

### 2.3 Mobilize

**Effect:**

Move two different friendly pieces by up to 1 tile each.

Recommended implementation:

- The player chooses two distinct friendly pieces.
- Each chosen piece may move up to 1 orthogonal tile.
- The moves are applied sequentially.
- The same piece cannot be moved twice.

No formation enhancement.

Important:
- This card may create a high branching factor.
- Implement legal-action generation carefully.
- Consider allowing only exactly two pieces if both have legal moves, but allow one-piece partial mobilization if no two-piece move exists.

---

### 2.4 Capture / Net Launcher

This is one card with two modes.

#### Base Mode: Capture

**Effect:**

Capture an adjacent enemy piece.

Rules:

- Range: 1 tile orthogonally.
- If successful, the enemy piece immediately returns to its spawn.
- The acting player gains capture points.

#### Enhanced Mode: Net Launcher

Net Launcher is the formation-enhanced version of Capture.

**Formation requirement:**

- At least two friendly pieces must be aligned in the same row or column.

**Effect:**

- The Capture card may target the first enemy piece along that row or column.
- The attack travels in a straight orthogonal line.
- It hits the first enemy piece in that line.
- Friendly pieces may define the line, but the shot should not pass through blocking pieces unless explicitly allowed.

Recommended initial rule:

- Net Launcher range: **3 tiles**.
- The target must be within range 3 from the front piece in the firing line.
- The shot cannot pass through any piece.
- If an enemy is hit, it is captured and returned to spawn.

Open implementation detail:
- Define precisely which piece is the “front” firing piece.
- Simpler option: generate all valid friendly aligned pairs, then generate rays extending outward from either end of the pair.

---

### 2.5 Swap

**Effect:**

Swap the locations of one friendly piece and one enemy piece within range.

Rules:

- Choose one friendly piece and one enemy piece.
- If their Manhattan distance is ≤ 3, swap their positions.
- Manhattan distance is:

```text
|x1 - x2| + |y1 - y2|
```

No formation enhancement.

Purpose:
- Break enemy formations.
- Pull enemies off the center.
- Enable tactical repositioning.
- Prevent formation strategies from becoming too stable.

---

## 3. Board Shape

### Initial Board

Start with a simple square grid.

Recommended first version:

- **5×5 grid**
- One center tile at coordinate `(2, 2)`

Coordinates:

```text
(0,0) (0,1) (0,2) (0,3) (0,4)
(1,0) (1,1) (1,2) (1,3) (1,4)
(2,0) (2,1) (2,2) (2,3) (2,4)
(3,0) (3,1) (3,2) (3,3) (3,4)
(4,0) (4,1) (4,2) (4,3) (4,4)
```

### Spawn Positions

Initial proposal:

Player A starts on the top row:

```text
(0,1), (0,2), (0,3)
```

Player B starts on the bottom row:

```text
(4,1), (4,2), (4,3)
```

If a captured piece returns to spawn and its original spawn tile is occupied, choose the nearest free spawn tile. If all spawn tiles are occupied, choose the nearest free tile to the spawn row.

This should be implemented deterministically.

### Future Board Generalization

Although the first implementation should use a grid, the code should be designed so the board can later be changed.

Represent the board internally as a graph:

- Nodes = board cells.
- Edges = legal movement connections.
- Grid is just one graph generator.
- Later experiments may use:
  - rectangular grids
  - grids with blocked cells
  - cross-shaped boards
  - ring-like boards
  - arbitrary graph boards

For the first implementation, line-based Net Launcher only needs to work on grid boards.

---

## 4. How the Game Should Be Implemented

Use Python.

Recommended architecture:

```text
src/
  game/
    state.py
    board.py
    cards.py
    rules.py
    actions.py
    engine.py
  agents/
    random_agent.py
    greedy_agent.py
    human_agent.py
    search_agent.py
  search/
    heuristic.py
    astar.py
    greedy_best_first.py
    bidirectional.py
    minimax.py
    expectimax.py
    mcts.py
  visualization/
    pygame_view.py
    text_view.py
  experiments/
    run_match.py
    tournament.py
    analyze_results.py
```

### State Representation

Game state should include:

- Current player.
- Turn number.
- Board/piece positions.
- Scores.
- Visible market cards.
- Deck composition or deck order.
- Discard pile.
- Random seed.
- Game configuration.

The state should be immutable or safely copyable because search agents will simulate future states.

### Action Representation

Each legal action should include:

- Chosen card index from the market.
- Card type.
- Selected piece or pieces.
- Target cell or target enemy piece.
- Any additional parameters, e.g. direction for Net Launcher.

### Legal Action Generation

Implement a single function:

```python
get_legal_actions(state) -> list[Action]
```

This is critical because all agents depend on it.

### State Transition

Implement:

```python
apply_action(state, action) -> State
```

This should:

1. Apply the card effect.
2. Update score if needed.
3. Move the used card to discard.
4. Draw replacement card.
5. Update center score if applicable.
6. Switch current player.
7. Advance turn counter.

For search, also implement deterministic transition variants where card draws are explicitly represented or sampled.

---

## 5. How to Visualize the Game

Start with a simple Pygame or text-based visualization.

### Minimal Text Visualization

Useful for debugging and search experiments.

Example:

```text
A . A . A
. . . . .
. . C . .
. . . . .
B . B . B

Visible cards: [Move1, Capture, Swap]
Score: A=3, B=6
Turn: A, round 12
```

### Pygame Visualization

Recommended visual elements:

- 5×5 grid.
- Player A pieces in one color.
- Player B pieces in another color.
- Center tile highlighted.
- Visible card market displayed beside the board.
- Current scores.
- Current turn/player.
- Last action log.

For the first version, visuals do not need animations. Static updates after each move are enough.

### Human Interaction

Human player should be able to:

- Click a visible card.
- Click piece(s).
- Click target location or enemy target.
- Confirm action.

If this takes too long, allow text input for human actions first.

---

## 6. Agents to Implement

### 6.1 Random Agent

Chooses uniformly from legal actions.

Purpose:
- Baseline.
- Debugging.
- Stress-testing game mechanics.

### 6.2 Greedy Agent

Evaluates each immediate successor state using the heuristic and chooses the best action.

Purpose:
- Simple heuristic baseline.
- Helps validate heuristic quality.

### 6.3 Human Agent

Allows a human to play through text or Pygame UI.

Purpose:
- Debugging.
- Qualitative evaluation.
- Demonstration.

### 6.4 Search-Based Agent

A configurable agent that can use different search methods.

Should support:

- Depth limit.
- Time limit.
- Node expansion limit.
- Heuristic function.
- Optional pruning.
- Optional stochastic rollouts.

---

## 7. Search Algorithms to Implement

Important note:

A*, greedy best-first, and bidirectional search are naturally pathfinding/planning algorithms. This is an adversarial stochastic game, so they do not fit as directly as minimax/expectimax/MCTS.

Still, because this is a Search Methods course, we can implement them in carefully defined ways.

### 7.1 Pure Heuristic Search / Greedy Best-First

Use the heuristic to select promising future states.

Possible implementation:

- Search forward from the current state.
- Expand states according to best heuristic score.
- Ignore opponent optimality or model opponent using a simple policy.
- Return the first action on the best found trajectory.

This is not a perfect game-theoretic agent, but it is useful as a search baseline.

### 7.2 A* Search

Define an internal planning objective.

Possible A* target:

- Reach a high-value tactical state within a limited horizon.
- Example goal:
  - occupy center,
  - create Net Launcher formation,
  - threaten capture,
  - or achieve score lead.

A* formulation:

```text
g(n) = number of turns/actions used
h(n) = estimated distance to tactical goal
f(n) = g(n) + h(n)
```

Recommended A* experiments:
- A* to center.
- A* to create a Net Launcher formation.
- A* to set up a capture.

A* should probably be used as a tactical planner inside an agent, not as the only game-playing algorithm.

### 7.3 Bidirectional Search

Bidirectional search is hard in a stochastic adversarial game, but can be applied to tactical subproblems.

Recommended formulation:

- Forward search from current piece configuration.
- Backward search from a desired tactical pattern.
- Example target:
  - two friendly pieces aligned with enemy in range,
  - friendly piece on center,
  - enemy within swap range.

Use this for analysis and as an optional planning module.

Do not overinvest in bidirectional search until the basic game and agents work.

### 7.4 Minimax

Implement depth-limited minimax as a deterministic baseline.

Simplification:
- Treat visible card replacement as deterministic or use expected value over possible replacements.
- Alternatively ignore card replacement during shallow minimax.

### 7.5 Expectimax / Expectiminimax

This is the best fit for the game.

The tree contains:

- Max nodes: current player decisions.
- Min nodes: opponent decisions.
- Chance nodes: random replacement card from the deck.

This should be the main search-based agent.

### 7.6 Monte Carlo Tree Search

Implement MCTS as a strong alternative search agent.

Use:

- Selection with UCB1.
- Expansion using legal actions.
- Simulation using random or heuristic rollout policy.
- Backpropagation using game outcome or score difference.

MCTS is useful because the game has high branching factor and stochastic card draws.

---

## 8. Heuristic Function

The heuristic should evaluate a state from the perspective of a player.

Initial heuristic:

```text
H(state, player) =
  w_score * score_difference
+ w_center * center_control
+ w_progress * center_distance_advantage
+ w_capture * capture_threats
+ w_net * net_launcher_potential
+ w_swap * swap_potential
+ w_safety * piece_safety
+ w_mobility * legal_action_count
```

### Components

#### Score Difference

```text
my_score - opponent_score
```

Most important component.

#### Center Control

Reward:

- occupying center,
- being close to center,
- having more pieces near center.

#### Center Distance Advantage

Use Manhattan distance from each player's pieces to the center.

Example:

```text
sum(opponent_distances_to_center) - sum(my_distances_to_center)
```

Lower distance is better for the player.

#### Capture Threats

Reward states where the player can capture on the next move.

Count:

- adjacent enemies,
- enemies hittable by Net Launcher.

#### Net Launcher Potential

Reward formations:

- two friendly pieces aligned in row/column,
- enemy on same line within possible range,
- pieces close to forming alignment.

#### Swap Potential

Reward useful swaps:

- enemy on center within swap range,
- enemy formation that can be broken,
- friendly piece that can be swapped into center.

#### Piece Safety

Penalty for:

- pieces adjacent to enemy,
- pieces in enemy Net Launcher line,
- pieces vulnerable to swap + capture.

#### Mobility

Reward having many legal actions, but keep this weight low because it may dominate.

### Initial Weights

Start with:

```python
weights = {
    "score": 100,
    "center": 10,
    "center_distance": 2,
    "capture_threat": 15,
    "net_potential": 20,
    "swap_potential": 8,
    "safety": 10,
    "mobility": 1,
}
```

Weights should be configurable for experiments.

---

## 9. How to Cut / Trim the Search Tree

The branching factor is a major concern, especially with cards like Mobilize and Swap.

Implement several trimming options.

### 9.1 Depth Limit

Always use a depth limit for game-tree search.

Recommended initial depths:

```text
depth = 1, 2, 3
```

Depth 4 may be expensive.

### 9.2 Beam Search / Top-K Action Filtering

Before expanding a node:

1. Generate all legal actions.
2. Score immediate successor states with the heuristic.
3. Keep only the top K actions.

Example:

```text
K = 5, 10, 20
```

This is probably the most important practical pruning method.

### 9.3 Alpha-Beta Pruning

For deterministic minimax, implement alpha-beta pruning.

For expectiminimax, alpha-beta is less straightforward because of chance nodes. Use action ordering and top-K filtering instead.

### 9.4 Monte Carlo Rollouts

For MCTS:

- Use random rollouts first.
- Then implement heuristic-guided rollouts.
- Use fixed simulation budget.

Example budgets:

```text
100, 500, 1000 simulations per move
```

### 9.5 Progressive Widening

Useful for MCTS when there are many legal actions.

Instead of expanding all legal actions immediately, gradually add actions as visit count increases.

### 9.6 Action Type Filtering

Optional.

Examples:

- If a capture is available, prioritize capture actions.
- If center is empty, prioritize moves toward center.
- If Net Launcher is available, prioritize it.
- If the player is far behind, prioritize capture threats.

Be careful: this can bias the agent too strongly. Keep it configurable.

### 9.7 Transposition Table

Cache evaluated states.

Use a hash of:

- piece positions,
- current player,
- score,
- visible market,
- remaining deck composition if needed.

This can significantly reduce repeated search.

---

## 10. Experiments to Run

### Agent Comparisons

Run tournaments:

- Random vs Random
- Greedy vs Random
- Greedy vs Greedy
- Search vs Random
- Search vs Greedy
- Expectimax vs MCTS
- A* tactical planner vs Greedy

### Search Depth

Evaluate:

- win rate by depth,
- average decision time,
- nodes expanded,
- score difference.

### Deck Composition

Test different deck types:

#### Balanced Deck

```text
Move1: 8
Move2: 6
Mobilize: 5
Capture: 5
Swap: 4
```

#### Rush Deck

```text
Move1: 6
Move2: 10
Mobilize: 8
Capture: 3
Swap: 3
```

#### Combat/Formations Deck

```text
Move1: 6
Move2: 4
Mobilize: 5
Capture: 9
Swap: 6
```

### Board Size

Start with:

- 5×5 grid.

Later test:

- 7×7 grid.
- 5×5 with blocked cells.
- non-rectangular grid shape.

### Heuristic Ablation

Compare heuristic variants:

- score only,
- score + center,
- score + center + capture threats,
- full heuristic.

### Runtime / Branching Factor Analysis

Measure:

- average legal actions per turn,
- legal actions by card type,
- search nodes expanded,
- time per move.

This is important because branching factor is one of the main design concerns.

---

## 11. Configuration

Use a config file or Python dataclass for all tunable parameters:

```python
GameConfig(
    board_size=(5, 5),
    pieces_per_player=3,
    turns_per_player=50,
    market_size=3,
    center_score=1,
    capture_score=3,
    swap_range=3,
    net_range=3,
    deck_composition={
        "move1": 8,
        "move2": 6,
        "mobilize": 5,
        "capture": 5,
        "swap": 4,
    },
)
```

---

## 12. Implementation Milestones

### Milestone 1 — Core Game

- Board representation.
- State representation.
- Card definitions.
- Legal action generation.
- Apply action.
- Random agent.
- Text visualization.

### Milestone 2 — Playability

- Human agent.
- Pygame visualization.
- Match runner.
- Logging.

### Milestone 3 — Heuristics

- Implement heuristic function.
- Greedy agent.
- Heuristic debugging tools.

### Milestone 4 — Search

- Minimax.
- Expectimax / expectiminimax.
- MCTS.
- A* tactical planner.
- Optional bidirectional tactical planner.

### Milestone 5 — Experiments

- Tournament framework.
- Save results to CSV.
- Plot win rates, runtime, nodes expanded, branching factor.
- Run deck and board experiments.

---

## 13. Open Design Decisions to Confirm

Before implementing too much, confirm these:

1. Should center scoring happen at the end of every player turn or at the end of each round?
2. Should a piece be allowed to stay still when playing Move 1 / Move 2 / Mobilize?
3. Should Swap allow friendly-enemy only, or any two pieces?
4. Should Net Launcher range be exactly 3 or configurable from the start?
5. Should Net Launcher require adjacent friendly pieces, or merely two friendly pieces aligned in the same row/column?
6. Should captured pieces return to a specific spawn tile or the nearest available spawn tile?
7. Should the deck be modeled as an ordered shuffled list or only as a remaining card-count distribution for search?
8. Should the first implementation prioritize Pygame visuals or text-based playability?

Recommended defaults:

```text
1. End of player turn.
2. Up to movement range, but not zero unless no move exists.
3. Friendly-enemy only.
4. Configurable, default 3.
5. Same row/column, not necessarily adjacent.
6. Nearest available spawn tile.
7. Ordered deck for actual play, card-count distribution for expectimax.
8. Text first, Pygame second.
```
