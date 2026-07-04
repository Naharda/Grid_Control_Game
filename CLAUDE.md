# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Context

"Graph Card Control" — a custom two-player, turn-based, stochastic, perfect-information strategy game built as a university final project for Search Methods in AI (comparing search-based agents against baseline agents). The game design spec is `graph_card_control_codex_plan.md` (default rules follow it), the lab report draft is `graph_card_control_report.md`, and the course submission guidelines are `project_instructions_en.md`. The root CSV files are legacy outputs from the pre-mode `tournament.py`; new experiments live under `modes/`.

## Commands

Python 3.10+; dependencies are just `pytest` and `pygame` (`pip install -r requirements.txt`).

```bash
pytest                                          # run all tests (pytest.ini sets pythonpath=src)
pytest tests/test_core_game.py::test_name       # run a single test

python start_game.py --a human --b greedy --show-initial   # text-mode match
python start_game.py --gui --a human --b greedy            # Pygame GUI (also: python visual_game.py)
python start_game.py --gui --mode baseline --a human --record   # play a mode; save the game CSV
python src/experiments/run_match.py --a greedy --b random --log

python src/experiments/create_mode.py NAME --agents greedy minimax   # define a mode (fails if it exists)
python src/experiments/run_mode.py NAME                              # play all pairs, write results + game logs
python src/experiments/reconstruct_game.py NAME greedy minimax 0 --gui  # replay/validate a recorded game
python src/experiments/analyze_results.py modes/NAME/results/greedy_minimax.csv

python src/experiments/tournament.py --a expectimax --b greedy --games 20 --out results.csv  # legacy
```

Agent names accepted by all CLIs: `human`, `random`, `rule`, `greedy`, `minimax`, `expectimax`, `mcts` (`human` is not allowed inside a mode; play modes via `--mode` + `--a human`).

## Game modes and data files

Experiments are packaged as **game modes**. Data lives at the repo root:

```
boards/<name>.json          # dimensions, spawns, capture cells (+points), blocked cells
decks/<name>.json           # card name -> count (card behavior stays hard-coded)
modes/<mode_name>/
    config.json             # created BEFORE running (create_mode.py); never overwritten
    results/<a>_<b>.csv     # game,agent_a,agent_b,winner,score_a,score_b (one file per ordered pair)
    games/<a>_<b>/<i>.csv   # per-turn move log per game
    games/{gui,text}/…      # hand-played games saved by --record
```

- `config.json` embeds full **board/deck snapshots** (plus names) so a mode reproduces even if `boards/`/`decks/` files change later; `load_mode` warns on drift. It also records rules (turns, market size, capture score, ranges), `heuristic_weights`, agents with their exact hyperparameters, `game_seeds`, and `agent_seed_policy` (`derived` fills null agent seeds with `game_seed*2+side` for reproducibility).
- `run_mode.py` runs **every ordered pair** (A-vs-B and B-vs-A, mirrors once) with the same seeds in both orientations.
- **Coordinate conventions:** board/deck JSON uses engine-native `[row, col]` (0-based). The games CSV serializes positions as `"<col>-<row>"` — column first! The inversion exists only in `pos_to_str`/`parse_pos` (`src/game/match_log.py`).
- **Games CSV format** (`game.match_log`): each row is a start-of-turn snapshot (`turn`, `player` 0=A/1=B, scores, market slots `card_0..`); the `action`/`card_drawn`/`src_*`/`dst_*` columns describe the **previous** turn's move (`-1`/`None` in row 0), and a trailing row carries the final move. `card_drawn` equals that row's `card_<action>`. For captures `src_0` is the actor (net: launched piece, `src_1` = launcher), `dst_0` the captured piece's tile. `replay_rows` reconstructs and validates a trajectory from these rows using forced draws.

## Architecture

### Import root is `src/`, not the repo root

All modules import as `game.*`, `agents.*`, `search.*`, `experiments.*`, `visualization.*` — never `src.game.*`. Root entry points (`start_game.py`, `visual_game.py`) and the experiment scripts insert `src` into `sys.path` themselves; pytest gets it from `pythonpath = src` in `pytest.ini`. Any new script needs the same shim or `PYTHONPATH=src`.

### Layers (dependency order: game ← search ← agents ← experiments/visualization)

- **`game/`** — pure rules engine. `GameState` (`state.py`) is a frozen dataclass; all transitions are pure functions in `rules.py` (`get_legal_actions`, `apply_action`) returning new states via `state.with_updates(...)`. `engine.play_match` loops a full match (optional `on_step(before, action|None, after)` observer, fired for pass turns too) and returns a `MatchResult`. `GameConfig` (`config.py`) holds all tunables; `scoring_cells` resolves `capture_cells` (position→points) or falls back to `{center: center_score}`. `setup_loader.py` loads/validates board & deck JSON into config kwargs; `match_log.py` is the games-CSV writer/replayer.
- **`search/`** — two distinct kinds of module: full decision procedures over game states (`minimax.py`, `expectimax.py`, `mcts.py`) and single-agent tactical pathfinding helpers (`astar.py`, `greedy_best_first.py`, `bidirectional.py`). Goal cells are the config's `scoring_cells` (nearest-cell distance). `heuristic.evaluate_state` is the shared state evaluation used by greedy, minimax, expectimax, and MCTS rollouts; its weights come from `GameConfig.heuristic_weights` (the `center`/`center_distance` keys now mean capture-cell control/distance).
- **`agents/`** — implement `Agent.choose_action(state, legal_actions)` (`base.py`). `SearchAgent` wraps minimax/expectimax; `MCTSAgent` wraps MCTS.
- **`experiments/`** — `run_match.py` holds `AGENT_SPECS`/`build_agent(name, params)`, the single agent registry (defaults recorded into mode configs). `modes.py` is mode config I/O; `create_mode.py`/`run_mode.py`/`reconstruct_game.py` are the mode CLIs. `tournament.py` is the legacy single-pair runner.
- **`visualization/`** — `text_view.render_state` (capture cells as `+N`, blocked as `##`) and the Pygame viewer (`pygame_view.run_pygame_game`), which supports human click-play, history review (also of reconstructed games via `history=`), auto-play, and translucent `+N` labels on capture cells.

**Adding a new agent** means adding one `AGENT_SPECS` entry in `src/experiments/run_match.py` (name → class + default params); all CLIs share `AGENT_NAMES`.

### Stochasticity and chance nodes

The only randomness is the card drawn to refill the 3-card public market after a play. The RNG state is threaded through `GameState.rng_state`, so games are fully deterministic given `GameConfig.seed` (default `1`; modes vary the seed per game via `game_seeds`). For search over chance nodes, `apply_action(state, action, draw_card=...)` forces a specific replacement card and `rules.possible_draws()` gives the draw distribution — this is how expectimax expands chance nodes exactly, and how `replay_rows` reproduces recorded games. `tests/test_backcompat.py` locks golden seeded trajectories — update it deliberately (only when game behavior is *meant* to change).

### Cards → actions

Each legal action is one market card plus its parameters (`Action` in `game/actions.py`): MOVE1/MOVE2 (move one piece 1–2 steps), MOBILIZE (move two different pieces 1 step each; falls back to `mode="partial"` single-piece moves when no pair works), CAPTURE (adjacent capture, or "net" ray capture fired outward from a pair of orthogonally adjacent friendly pieces, `mode="net"`; captured pieces respawn at their spawn area with a deterministic fallback), SWAP (swap with an enemy piece within range). Captures carry a no-op `PieceMove` naming the acting piece, and net captures set `launcher_id` — required by the games-CSV log. Scoring: +3 per capture (`capture_score`), plus each occupied capture cell's points at end of turn; game lasts 50 turns per player, highest score wins.
