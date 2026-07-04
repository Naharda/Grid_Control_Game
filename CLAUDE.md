# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Context

"Graph Card Control" — a custom two-player, turn-based, stochastic, perfect-information strategy game built as a university final project for Search Methods in AI (comparing search-based agents against baseline agents). The game design spec is `graph_card_control_codex_plan.md` (default rules follow it), the lab report draft is `graph_card_control_report.md`, and the course submission guidelines are `project_instructions_en.md`. The root CSV files are experiment outputs from tournament runs.

## Commands

Python 3.10+; dependencies are just `pytest` and `pygame` (`pip install -r requirements.txt`).

```bash
pytest                                          # run all tests (pytest.ini sets pythonpath=src)
pytest tests/test_core_game.py::test_name       # run a single test

python start_game.py --a human --b greedy --show-initial   # text-mode match
python start_game.py --gui --a human --b greedy            # Pygame GUI (also: python visual_game.py)
python src/experiments/run_match.py --a greedy --b random --log
python src/experiments/tournament.py --a expectimax --b greedy --games 20 --out results.csv
python src/experiments/analyze_results.py results.csv      # win counts + avg score diff from a tournament CSV
```

Agent names accepted by all CLIs: `human`, `random`, `rule`, `greedy`, `minimax`, `expectimax`, `mcts`.

## Architecture

### Import root is `src/`, not the repo root

All modules import as `game.*`, `agents.*`, `search.*`, `experiments.*`, `visualization.*` — never `src.game.*`. Root entry points (`start_game.py`, `visual_game.py`) and the experiment scripts insert `src` into `sys.path` themselves; pytest gets it from `pythonpath = src` in `pytest.ini`. Any new script needs the same shim or `PYTHONPATH=src`.

### Layers (dependency order: game ← search ← agents ← experiments/visualization)

- **`game/`** — pure rules engine. `GameState` (`state.py`) is a frozen dataclass; all transitions are pure functions in `rules.py` (`get_legal_actions`, `apply_action`) returning new states via `state.with_updates(...)`. `engine.play_match` loops a full match and returns a `MatchResult`. `GameConfig` (`config.py`) holds all tunables: board size, scoring, deck composition, spawn points, and the `heuristic_weights` dict used by the shared evaluation function.
- **`search/`** — two distinct kinds of module: full decision procedures over game states (`minimax.py`, `expectimax.py`, `mcts.py`) and single-agent tactical pathfinding helpers (`astar.py`, `greedy_best_first.py`, `bidirectional.py`, e.g. shortest path to center). `heuristic.evaluate_state` is the shared state evaluation used by greedy, minimax, expectimax, and MCTS rollouts; its weights come from `GameConfig.heuristic_weights`.
- **`agents/`** — implement `Agent.choose_action(state, legal_actions)` (`base.py`). `SearchAgent` wraps minimax/expectimax; `MCTSAgent` wraps MCTS.
- **`experiments/`** — `run_match.py` holds `build_agent()`, the single agent registry (with each agent's default depth/top_k/simulation parameters). `tournament.py` runs N games varying `GameConfig(seed=game_id)` and writes CSV.
- **`visualization/`** — `text_view.render_state` and the Pygame viewer (`pygame_view.run_pygame_game`), which supports human click-play, history review, and auto-play of computer moves.

**Adding a new agent** means updating `build_agent()` in `src/experiments/run_match.py` *and* the `AGENTS` list / argparse choices in `start_game.py`, `visual_game.py`, and `run_match.py`.

### Stochasticity and chance nodes

The only randomness is the card drawn to refill the 3-card public market after a play. The RNG state is threaded through `GameState.rng_state`, so games are fully deterministic given `GameConfig.seed` (default `1` — `initial_state()` always produces the same game; tournaments vary the seed per game). For search over chance nodes, `apply_action(state, action, draw_card=...)` forces a specific replacement card and `rules.possible_draws()` gives the draw distribution — this is how expectimax expands chance nodes exactly.

### Cards → actions

Each legal action is one market card plus its parameters (`Action` in `game/actions.py`): MOVE1/MOVE2 (move one piece 1–2 steps), MOBILIZE (move two different pieces 1 step each; falls back to `mode="partial"` single-piece moves when no pair works), CAPTURE (adjacent capture, or "net" ray capture fired outward from a pair of orthogonally adjacent friendly pieces, `mode="net"`; captured pieces respawn at their spawn area with a deterministic fallback), SWAP (swap with an enemy piece within range). Scoring: +3 per capture, +1 for occupying the center at end of turn; game lasts 50 turns per player, highest score wins.
