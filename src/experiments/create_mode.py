"""Create a game-mode config before running it.

Only the mode name and agents are required; everything else defaults to the
current standard setup. The config embeds full board/deck snapshots plus all
rule values and agent hyperparameters, so a mode is reproducible on its own.

    python src/experiments/create_mode.py baseline --agents greedy minimax
    python src/experiments/create_mode.py everyone --all-agents --games 20
    python src/experiments/create_mode.py deep --agents minimax mcts \
        --param minimax.depth=3 --param mcts.simulations=500
    python src/experiments/create_mode.py custom --agents greedy random --interactive
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.modes import SEED_POLICIES, save_mode
from experiments.run_match import AGENT_NAMES, NON_HUMAN_AGENT_NAMES, build_agent, default_params
from game.config import GameConfig
from game.setup_loader import REPO_ROOT, load_board, load_deck

_DEFAULTS = GameConfig()


def parse_seeds(text: str) -> list[int]:
    """Parse "0:20" (half-open range) or "1,5,9" / "7" (explicit list)."""
    text = text.strip()
    if ":" in text:
        start, stop = text.split(":", 1)
        seeds = list(range(int(start), int(stop)))
    else:
        seeds = [int(part) for part in text.split(",") if part.strip()]
    if not seeds:
        raise ValueError(f"No seeds in {text!r}")
    return seeds


def parse_param_overrides(items: list[str]) -> dict[str, dict]:
    overrides: dict[str, dict] = {}
    for item in items:
        try:
            target, value = item.split("=", 1)
            agent, key = target.split(".", 1)
        except ValueError:
            raise SystemExit(f"--param expects <agent>.<key>=<value>, got {item!r}")
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            parsed = value
        overrides.setdefault(agent, {})[key] = parsed
    return overrides


def code_version() -> str:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=REPO_ROOT, capture_output=True, text=True, timeout=5,
        )
        return out.stdout.strip() or "unknown"
    except OSError:
        return "unknown"


def _prompt(label: str, current, cast=str):
    try:
        raw = input(f"{label} [{current}]: ").strip()
    except EOFError:
        return current
    if not raw:
        return current
    return cast(raw)


def interactive_fill(args: argparse.Namespace) -> None:
    print("Blank keeps the value in brackets.")
    args.description = _prompt("description", args.description)
    args.board = _prompt("board", args.board)
    args.deck = _prompt("deck", args.deck)
    args.games = _prompt("games", args.games, int)
    args.seeds = _prompt("seeds (start:stop or comma list)", args.seeds or f"0:{args.games}")
    args.turns = _prompt("turns per player", args.turns, int)
    args.market_size = _prompt("market size", args.market_size, int)
    args.capture_score = _prompt("capture score", args.capture_score, int)
    args.swap_range = _prompt("swap range", args.swap_range, int)
    args.net_range = _prompt("net range", args.net_range, int)
    args.seed_policy = _prompt(f"agent seed policy {SEED_POLICIES}", args.seed_policy)


def interactive_params(name: str, params: dict) -> dict:
    filled = {}
    for key, value in params.items():
        try:
            raw = input(f"{name}.{key} [{value}]: ").strip()
        except EOFError:
            raw = ""
        if not raw:
            filled[key] = value
            continue
        try:
            filled[key] = json.loads(raw)
        except json.JSONDecodeError:
            filled[key] = raw
    return filled


def build_mode_config(args: argparse.Namespace) -> dict:
    overrides = parse_param_overrides(args.param)
    unknown_override_agents = set(overrides) - set(args.agents)
    if unknown_override_agents:
        raise SystemExit(f"--param given for agents not in --agents: {sorted(unknown_override_agents)}")

    agents = []
    for name in args.agents:
        params = {**default_params(name), **overrides.get(name, {})}
        if args.interactive:
            params = interactive_params(name, params)
        build_agent(name, params)  # dry-run: unknown keys / bad values fail here
        agents.append({"name": name, "params": params})

    seeds = parse_seeds(args.seeds) if args.seeds else list(range(args.games))
    return {
        "schema_version": 1,
        "mode_name": args.name,
        "description": args.description,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "code_version": code_version(),
        "board": {"name": str(args.board), "definition": load_board(args.board)},
        "deck": {"name": str(args.deck), "definition": load_deck(args.deck)},
        "rules": {
            "turns_per_player": args.turns,
            "market_size": args.market_size,
            "capture_score": args.capture_score,
            "swap_range": args.swap_range,
            "net_range": args.net_range,
        },
        "heuristic_weights": dict(_DEFAULTS.heuristic_weights),
        "agents": agents,
        "num_games": len(seeds),
        "game_seeds": seeds,
        "agent_seed_policy": args.seed_policy,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Define a new game mode (fails if it already exists).")
    parser.add_argument("name", help="Mode name; creates modes/<name>/config.json.")
    agent_group = parser.add_mutually_exclusive_group(required=True)
    agent_group.add_argument("--agents", nargs="+", metavar="AGENT",
                             help=f"Agents to compare (from: {', '.join(NON_HUMAN_AGENT_NAMES)}).")
    agent_group.add_argument("--all-agents", action="store_true",
                             help="Shorthand for --agents with every non-human agent.")
    parser.add_argument("--board", default="default", help="Board name in boards/ (or path to a board JSON).")
    parser.add_argument("--deck", default="default", help="Deck name in decks/ (or path to a deck JSON).")
    parser.add_argument("--games", type=int, default=20, help="Number of games per ordered agent pair.")
    parser.add_argument("--seeds", help='Explicit game seeds: "0:20" (range) or "1,5,9" (list). Default 0:<games>.')
    parser.add_argument("--turns", type=int, default=_DEFAULTS.turns_per_player, help="Turns per player.")
    parser.add_argument("--market-size", type=int, default=_DEFAULTS.market_size)
    parser.add_argument("--capture-score", type=int, default=_DEFAULTS.capture_score)
    parser.add_argument("--swap-range", type=int, default=_DEFAULTS.swap_range)
    parser.add_argument("--net-range", type=int, default=_DEFAULTS.net_range)
    parser.add_argument("--description", default="")
    parser.add_argument("--param", action="append", default=[], metavar="AGENT.KEY=VALUE",
                        help="Agent hyperparameter override, e.g. minimax.depth=3. Repeatable.")
    parser.add_argument("--seed-policy", default="derived", choices=SEED_POLICIES,
                        help="How null agent seeds are filled at run time.")
    parser.add_argument("--interactive", action="store_true", help="Prompt for every field (blank = default).")
    parser.add_argument("--modes-root", type=Path, help="Override the modes/ directory (mainly for tests).")
    args = parser.parse_args()

    if args.all_agents:
        args.agents = list(NON_HUMAN_AGENT_NAMES)

    for name in args.agents:
        if name == "human":
            raise SystemExit("The 'human' agent cannot be used in a mode; play modes via start_game.py --mode.")
        if name not in AGENT_NAMES:
            raise SystemExit(f"Unknown agent {name!r}; choose from {NON_HUMAN_AGENT_NAMES}")
    if len(set(args.agents)) != len(args.agents):
        raise SystemExit("Duplicate agent names are not allowed (results files would collide).")

    if args.interactive:
        interactive_fill(args)

    config = build_mode_config(args)
    try:
        path = save_mode(config, root=args.modes_root)
    except FileExistsError as exc:
        raise SystemExit(str(exc))
    print(f"Created {path}")
    pairs = len(config["agents"]) ** 2
    print(f"{config['num_games']} games x {pairs} ordered pair(s); run with:")
    print(f"  python src/experiments/run_mode.py {config['mode_name']}")


if __name__ == "__main__":
    main()
