"""Game-mode config I/O and path helpers.

A game mode lives in `modes/<mode_name>/` at the repo root:

    modes/<mode_name>/
        config.json                        # created before any run
        results/<agent1>_<agent2>.csv      # aggregate results per ordered pair
        games/<agent1>_<agent2>/<i>.csv    # per-game move logs

config.json embeds full board/deck snapshots so results stay reproducible
even if boards/*.json or decks/*.json change later.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from game.config import GameConfig
from game.setup_loader import (
    REPO_ROOT,
    board_config_kwargs,
    build_config,
    deck_config_kwargs,
    load_board,
    load_deck,
    validate_board,
    validate_deck,
)

MODES_ROOT = REPO_ROOT / "modes"

RULE_FIELDS = ("turns_per_player", "market_size", "capture_score", "swap_range", "net_range")
SEED_POLICIES = ("derived", "null-passthrough")


def mode_dir(name: str, root: Path | None = None) -> Path:
    return (root or MODES_ROOT) / name


def config_path(name: str, root: Path | None = None) -> Path:
    return mode_dir(name, root) / "config.json"


def results_path(mode_name: str, a: str, b: str, root: Path | None = None) -> Path:
    return mode_dir(mode_name, root) / "results" / f"{pair_key(a, b)}.csv"


def games_dir(mode_name: str, a: str, b: str, root: Path | None = None) -> Path:
    return mode_dir(mode_name, root) / "games" / pair_key(a, b)


def pair_key(a: str, b: str) -> str:
    return f"{a}_{b}"


def ordered_pairs(agent_names: list[str]) -> list[tuple[str, str]]:
    """All ordered pairs of distinct agents, plus each mirror pair once."""
    pairs: list[tuple[str, str]] = []
    for a in agent_names:
        for b in agent_names:
            if (a, b) not in pairs:
                pairs.append((a, b))
    return pairs


def save_mode(config: dict, root: Path | None = None, *, overwrite: bool = False) -> Path:
    validate_mode(config)
    path = config_path(config["mode_name"], root)
    if path.exists() and not overwrite:
        raise FileExistsError(f"Mode {config['mode_name']!r} already exists at {path}")
    directory = path.parent
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "results").mkdir(exist_ok=True)
    (directory / "games").mkdir(exist_ok=True)
    path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    return path


def load_mode(name: str, root: Path | None = None) -> dict:
    path = config_path(name, root)
    if not path.exists():
        modes_root = root or MODES_ROOT
        available = sorted(p.parent.name for p in modes_root.glob("*/config.json")) if modes_root.exists() else []
        raise FileNotFoundError(f"No mode named {name!r} ({path}); available: {available}")
    mode = json.loads(path.read_text(encoding="utf-8"))
    validate_mode(mode, source=str(path))
    _warn_on_snapshot_drift(mode)
    return mode


def validate_mode(mode: dict, source: str = "<mode>") -> None:
    for field in ("mode_name", "board", "deck", "rules", "agents", "game_seeds"):
        if field not in mode:
            raise ValueError(f"{source}: missing required field {field!r}")
    for kind in ("board", "deck"):
        entry = mode[kind]
        if not (isinstance(entry, dict) and "name" in entry and isinstance(entry.get("definition"), dict)):
            raise ValueError(f"{source}: {kind!r} must contain 'name' and an embedded 'definition'")
    validate_board(mode["board"]["definition"], source=f"{source}: board definition")
    validate_deck(mode["deck"]["definition"], source=f"{source}: deck definition")
    rules = mode["rules"]
    for field in RULE_FIELDS:
        if not (isinstance(rules.get(field), int) and rules[field] >= 1):
            raise ValueError(f"{source}: rules.{field} must be a positive integer")
    agents = mode["agents"]
    if not (isinstance(agents, list) and agents):
        raise ValueError(f"{source}: 'agents' must be a non-empty list")
    names = []
    for entry in agents:
        if not (isinstance(entry, dict) and isinstance(entry.get("name"), str) and isinstance(entry.get("params"), dict)):
            raise ValueError(f"{source}: each agent needs 'name' and 'params', got {entry!r}")
        names.append(entry["name"])
    if len(set(names)) != len(names):
        raise ValueError(f"{source}: duplicate agent names {names} would collide in results/games paths")
    seeds = mode["game_seeds"]
    if not (isinstance(seeds, list) and seeds and all(isinstance(s, int) for s in seeds)):
        raise ValueError(f"{source}: 'game_seeds' must be a non-empty list of integers")
    policy = mode.get("agent_seed_policy", "derived")
    if policy not in SEED_POLICIES:
        raise ValueError(f"{source}: agent_seed_policy must be one of {SEED_POLICIES}")


def _warn_on_snapshot_drift(mode: dict) -> None:
    for kind, loader in (("board", load_board), ("deck", load_deck)):
        name = mode[kind]["name"]
        try:
            current = loader(name)
        except (FileNotFoundError, ValueError):
            continue
        if current != mode[kind]["definition"]:
            print(
                f"warning: {kind} {name!r} on disk differs from the snapshot embedded in mode "
                f"{mode['mode_name']!r}; the embedded snapshot is used",
                file=sys.stderr,
            )


def config_from_mode(mode: dict, seed: int | None = None) -> GameConfig:
    kwargs: dict = {"seed": seed}
    kwargs.update(board_config_kwargs(mode["board"]["definition"]))
    kwargs.update(deck_config_kwargs(mode["deck"]["definition"]))
    kwargs.update({field: mode["rules"][field] for field in RULE_FIELDS})
    if "heuristic_weights" in mode:
        kwargs["heuristic_weights"] = dict(mode["heuristic_weights"])
    return GameConfig(**kwargs)


def effective_agent_params(params: dict, policy: str, game_seed: int, side: int) -> dict:
    """Substitute a derived deterministic seed for null-seeded agents."""
    if policy == "derived" and "seed" in params and params["seed"] is None:
        return {**params, "seed": game_seed * 2 + side}
    return dict(params)


def entry_game_setup(
    mode_name: str | None = None,
    board: str | None = None,
    deck: str | None = None,
    seed: int | None = None,
    modes_root: Path | None = None,
) -> tuple[GameConfig, dict | None]:
    """Shared --mode/--board/--deck/--seed resolution for the entry-point CLIs.

    Returns the GameConfig plus the loaded mode dict (None without --mode).
    An unset seed falls back to the mode's first game seed, else 1.
    """
    if mode_name:
        if board or deck:
            raise SystemExit("--mode cannot be combined with --board/--deck")
        mode = load_mode(mode_name, root=modes_root)
        effective_seed = seed if seed is not None else mode["game_seeds"][0]
        return config_from_mode(mode, seed=effective_seed), mode
    board_def = load_board(board) if board else None
    deck_def = load_deck(deck) if deck else None
    return build_config(board=board_def, deck=deck_def, seed=seed if seed is not None else 1), None


def mode_agent_spec(mode: dict, cli_name: str | None, position: int) -> tuple[str, dict | None]:
    """Resolve an entry-point agent under --mode.

    An explicit CLI name wins (reusing the mode's recorded params when the
    name matches a mode agent); otherwise the mode's agent at `position`
    (wrapping, so single-agent modes fill both sides).
    """
    if cli_name:
        by_name = {entry["name"]: entry["params"] for entry in mode["agents"]}
        return cli_name, by_name.get(cli_name)
    entry = mode["agents"][position % len(mode["agents"])]
    return entry["name"], entry["params"]


def gui_record_path(mode_name: str, source: str, seed: int, timestamp: str, root: Path | None = None) -> Path:
    """Path for a hand-played game: modes/<m>/games/<source>/<timestamp>_seed<seed>.csv."""
    return mode_dir(mode_name, root) / "games" / source / f"{timestamp}_seed{seed}.csv"
