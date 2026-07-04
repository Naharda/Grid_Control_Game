# Graph Card Control — Official Rules

Graph Card Control is a two-player, turn-based abstract strategy game of perfect information. Both players see the entire board, all scores, the face-up card market, and the full composition of the deck. The only randomness is the order in which cards are drawn to refill the market.

All numeric values below (board size, scores, ranges, deck composition, game length) are the defaults defined in `GameConfig` (`src/game/config.py`) and are configurable.

## 1. Components

- A **5×5 grid board**. Cells are identified as `(row, column)`, with `(0, 0)` at the top-left. Row 0 is the top row; row 4 is the bottom row. Cells are connected **orthogonally** (up, down, left, right) — there is no diagonal adjacency.
- The **center tile** `(2, 2)`.
- **3 pieces per player**. Pieces belonging to the same player are identical in ability.
- A shared **deck of 28 action cards**:

  | Card | Copies |
  |------------|--------|
  | Move 1 | 8 |
  | Move 2 | 6 |
  | Mobilize | 5 |
  | Capture | 5 |
  | Swap | 4 |

## 2. Setup

1. Player A places their 3 pieces on their **spawn tiles**: `(0, 1)`, `(0, 2)`, `(0, 3)` (top row).
2. Player B places their 3 pieces on their spawn tiles: `(4, 1)`, `(4, 2)`, `(4, 3)` (bottom row).
3. Shuffle the deck and deal the top **3 cards face-up** to form the public **market**. The rest of the deck forms a face-down draw pile. (The deck's composition is public knowledge; only the draw order is unknown.)
4. Both players' scores start at **0**. Player A takes the first turn.

```
        col 0   1   2   3   4
row 0    .    A   A   A    .     ← Player A spawn row
row 1    .    .   .   .    .
row 2    .    .   ★   .    .     ★ = center tile (2,2)
row 3    .    .   .   .    .
row 4    .    B   B   B    .     ← Player B spawn row
```

## 3. Object of the Game

Score more points than your opponent by the time the game ends. Points are earned two ways:

- **+3 points** for each enemy piece you capture.
- **+1 point** at the end of each of your turns in which one of your pieces occupies the center tile.

## 4. Game Length and Winning

- The game lasts **50 turns per player** (100 turns total), alternating strictly between the players.
- The game ends once **both** players have taken all 50 of their turns.
- The player with the **higher score** wins. Equal scores are a **draw**.

## 5. Turn Structure

On your turn:

1. **Choose one** of the 3 face-up cards in the market.
2. **Perform its action** (see §6). You must choose a card and a use of it that is legal; you may not play a card "for no effect".
3. **Score the center**: if any of your pieces now occupies the center tile `(2, 2)`, gain **+1 point**. (Capture points, if any, were scored during the action itself.)
4. **Refill the market**: place the used card in the discard pile, then draw the top card of the deck into the empty market slot. If the deck is empty, shuffle the entire discard pile (including the card just used) to form a new deck, then draw.
5. Your turn ends and play passes to your opponent.

**Passing:** If no card in the market offers any legal action (extremely rare), your turn is skipped. The skipped turn still counts toward your 50 turns; the market is unchanged.

## 6. The Actions

Throughout this section, "occupied" means occupied by **any** piece, yours or the enemy's. Two pieces may never share a cell.

### 6.1 Move 1

Move **one** of your pieces exactly **1 step** to an orthogonally adjacent empty cell.

### 6.2 Move 2

Move **one** of your pieces **up to 2 steps** (1 or 2) along orthogonally connected cells.

- The piece travels along a path of adjacent cells; it may turn (e.g. one step down, one step right).
- The path may **not** pass through any occupied cell, and the destination must be empty.
- The piece must end on a different cell than it started.

### 6.3 Mobilize

Move **two different** friendly pieces **1 step each**.

- Both moves are resolved **simultaneously from the starting position**: each piece moves to an empty cell adjacent to where it started, evaluated before either piece has moved. In particular, one piece may **not** move into the cell the other piece is vacating this turn.
- The two pieces may not move to the same destination cell.
- **Partial fallback:** if there is no legal way to move two pieces, Mobilize may instead be used to move a single piece 1 step (like Move 1).

### 6.4 Capture

Remove one enemy piece from its position and score **+3 points**. Your own pieces do not move. There are two ways to capture; choose one target using either:

**(a) Melee capture.** Capture an enemy piece that is orthogonally adjacent to one of your pieces.

**(b) Net launcher.** Two of your pieces that are **orthogonally adjacent** (side by side in the same row or column — diagonal contact does not count) form a net. The net fires a ray **outward from each end of the pair** — along the shared line, away from the other piece — with a range of **3 cells**, so the target may have 0, 1, or 2 empty cells between it and the pair:

- The ray examines cells one at a time, moving outward along the pair's shared row or column.
- The **first occupied cell** the ray reaches stops it. If that cell holds an **enemy** piece, that piece may be captured. If it holds a **friendly** piece, the ray is blocked and nothing can be captured in that direction. Pieces beyond the first one can never be captured — the net cannot skip over pieces, only over empty cells.
- The ray does not extend past the board edge or beyond 3 cells.

```
Net example (X = your pieces, e = enemy, . = empty):

 . . e      The two X's are adjacent in a column, so one
 . . .      ray fires upward from the top X and another
 . . X      fires downward from the bottom X, up to 3
 . . X      cells each. The upward ray skips one empty
 . . .      cell, hits the enemy 'e' — it may be captured.
```

**Respawning.** A captured piece is not eliminated. It is immediately returned to its owner's spawn row: it is placed on the first free spawn tile (checked in the order the spawn tiles are listed in §2). If all three spawn tiles are occupied, it is placed on the free cell with the smallest Manhattan distance to any of its spawn tiles, ties broken by lower row, then lower column.

### 6.5 Swap

Exchange the positions of **one of your pieces** and **one enemy piece** whose Manhattan distance from it (|Δrow| + |Δcol|) is **at most 3**. No pieces are captured and no points are scored by the swap itself — though if it places your piece on the center tile, you score the center at the end of your turn as usual.

## 7. Clarifications

- **The market is shared.** Both players draw from the same three face-up cards; a card you leave behind will be available to your opponent.
- **Center scoring repeats.** The center is worth +1 at the end of *every* one of your turns in which you occupy it — parking a piece on the center yields a point per turn until it is moved, swapped away, or captured.
- **Capture cards don't reposition you.** Only Move 1, Move 2, Mobilize, and Swap change the location of your pieces.
- **Perfect information, stochastic refill.** Everything is visible at all times. Strategy under uncertainty concerns only *which card* will be drawn to refill the market slot — the probability of each card type is always computable from the known deck and discard contents.
