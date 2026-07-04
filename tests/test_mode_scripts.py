from __future__ import annotations

from types import SimpleNamespace

import pytest

import csv

from experiments.create_mode import build_mode_config, parse_param_overrides, parse_seeds
from experiments.modes import (
    config_from_mode,
    effective_agent_params,
    games_dir,
    load_mode,
    ordered_pairs,
    pair_key,
    results_path,
    save_mode,
)
from experiments.run_mode import run_mode
from game.config import GameConfig
from game.match_log import read_game_csv, replay_rows
from game.state import initial_state


def _creation_args(name="tiny", agents=("greedy", "random"), **overrides):
    args = SimpleNamespace(
        name=name,
        agents=list(agents),
        board="default",
        deck="default",
        games=2,
        seeds=None,
        turns=4,
        market_size=3,
        capture_score=3,
        swap_range=3,
        net_range=3,
        description="test mode",
        param=[],
        seed_policy="derived",
        interactive=False,
    )
    for key, value in overrides.items():
        setattr(args, key, value)
    return args


def _create_mode(tmp_path, **overrides):
    config = build_mode_config(_creation_args(**overrides))
    save_mode(config, root=tmp_path)
    return config


def test_parse_seeds() -> None:
    assert parse_seeds("0:4") == [0, 1, 2, 3]
    assert parse_seeds("1,5,9") == [1, 5, 9]
    assert parse_seeds("7") == [7]
    with pytest.raises(ValueError):
        parse_seeds("")


def test_parse_param_overrides() -> None:
    overrides = parse_param_overrides(["minimax.depth=3", "mcts.simulations=500", "minimax.method=minimax"])
    assert overrides == {"minimax": {"depth": 3, "method": "minimax"}, "mcts": {"simulations": 500}}


def test_ordered_pairs() -> None:
    assert ordered_pairs(["a", "b"]) == [("a", "a"), ("a", "b"), ("b", "a"), ("b", "b")]
    assert ordered_pairs(["a"]) == [("a", "a")]


def test_created_mode_records_defaults_and_params(tmp_path) -> None:
    config = _create_mode(tmp_path, agents=("greedy", "minimax"), param=["minimax.depth=3"])
    assert config["mode_name"] == "tiny"
    assert config["game_seeds"] == [0, 1]
    assert config["num_games"] == 2
    assert config["rules"]["turns_per_player"] == 4
    assert config["board"]["definition"]["rows"] == 5
    assert config["deck"]["definition"]["cards"]["move1"] == 8
    by_name = {entry["name"]: entry["params"] for entry in config["agents"]}
    assert by_name["minimax"] == {"method": "minimax", "depth": 3, "top_k": 10}
    assert by_name["greedy"] == {}


def test_create_rejects_existing_mode(tmp_path) -> None:
    _create_mode(tmp_path)
    with pytest.raises(FileExistsError, match="tiny"):
        _create_mode(tmp_path)


def test_create_rejects_unknown_param(tmp_path) -> None:
    with pytest.raises(ValueError, match="depth"):
        _create_mode(tmp_path, agents=("greedy",), param=["greedy.depth=3"])


def test_load_mode_round_trip(tmp_path) -> None:
    created = _create_mode(tmp_path)
    loaded = load_mode("tiny", root=tmp_path)
    assert loaded == created
    assert (tmp_path / "tiny" / "results").is_dir()
    assert (tmp_path / "tiny" / "games").is_dir()


def test_config_from_mode_matches_defaults(tmp_path) -> None:
    _create_mode(tmp_path, turns=50)
    mode = load_mode("tiny", root=tmp_path)
    config = config_from_mode(mode, seed=1)
    default = GameConfig()
    assert config.board_size == default.board_size
    assert config.scoring_cells == default.scoring_cells
    assert config.deck_composition == default.deck_composition
    assert config.turns_per_player == 50
    assert config.seed == 1


def test_effective_agent_params_seed_policy() -> None:
    assert effective_agent_params({"seed": None}, "derived", 7, 0) == {"seed": 14}
    assert effective_agent_params({"seed": None}, "derived", 7, 1) == {"seed": 15}
    assert effective_agent_params({"seed": 3}, "derived", 7, 1) == {"seed": 3}
    assert effective_agent_params({"seed": None}, "null-passthrough", 7, 1) == {"seed": None}
    assert effective_agent_params({}, "derived", 7, 0) == {}


def test_pair_key() -> None:
    assert pair_key("greedy", "random") == "greedy_random"


def _read_results(path):
    with open(path, newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_run_mode_produces_all_pair_files(tmp_path) -> None:
    _create_mode(tmp_path)
    mode = load_mode("tiny", root=tmp_path)
    run_mode(mode, root=tmp_path)

    for a, b in [("greedy", "greedy"), ("greedy", "random"), ("random", "greedy"), ("random", "random")]:
        results = _read_results(results_path("tiny", a, b, tmp_path))
        assert [row["game"] for row in results] == ["0", "1"]
        assert {row["agent_a"] for row in results} == {a}
        assert {row["agent_b"] for row in results} == {b}
        for i in range(2):
            game_file = games_dir("tiny", a, b, tmp_path) / f"{i}.csv"
            rows = read_game_csv(game_file)
            assert len(rows) == 2 * mode["rules"]["turns_per_player"] + 1


def test_run_mode_refuses_overwrite_without_force(tmp_path) -> None:
    _create_mode(tmp_path)
    mode = load_mode("tiny", root=tmp_path)
    run_mode(mode, root=tmp_path)
    with pytest.raises(SystemExit, match="--force"):
        run_mode(mode, root=tmp_path)
    run_mode(mode, root=tmp_path, force=True)


def test_mirror_mode_runs_single_pair(tmp_path) -> None:
    _create_mode(tmp_path, name="solo", agents=("greedy",))
    mode = load_mode("solo", root=tmp_path)
    run_mode(mode, root=tmp_path)
    results_dir = tmp_path / "solo" / "results"
    assert [p.name for p in sorted(results_dir.iterdir())] == ["greedy_greedy.csv"]


def test_swapped_orders_share_seeds(tmp_path) -> None:
    _create_mode(tmp_path)
    mode = load_mode("tiny", root=tmp_path)
    run_mode(mode, root=tmp_path)
    for i in range(2):
        ab = read_game_csv(games_dir("tiny", "greedy", "random", tmp_path) / f"{i}.csv")
        ba = read_game_csv(games_dir("tiny", "random", "greedy", tmp_path) / f"{i}.csv")
        market_keys = ["card_0", "card_1", "card_2"]
        assert [ab[0][k] for k in market_keys] == [ba[0][k] for k in market_keys]


def test_recorded_games_replay_and_match_results(tmp_path) -> None:
    _create_mode(tmp_path)
    mode = load_mode("tiny", root=tmp_path)
    run_mode(mode, root=tmp_path)
    for a, b in ordered_pairs(["greedy", "random"]):
        results = _read_results(results_path("tiny", a, b, tmp_path))
        for i, result_row in enumerate(results):
            seed = mode["game_seeds"][i]
            initial = initial_state(config_from_mode(mode, seed=seed))
            rows = read_game_csv(games_dir("tiny", a, b, tmp_path) / f"{i}.csv")
            states = replay_rows(initial, rows, validate=True)
            final = states[-1]
            assert final.scores["A"] == int(result_row["score_a"])
            assert final.scores["B"] == int(result_row["score_b"])
