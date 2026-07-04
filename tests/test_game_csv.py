from __future__ import annotations

from agents.random_agent import RandomAgent
from game.actions import Action, PieceMove
from game.cards import CardType
from game.config import GameConfig
from game.engine import play_match
from game.match_log import (
    GameCsvRecorder,
    action_columns,
    games_csv_header,
    parse_pos,
    pos_to_str,
    read_game_csv,
    replay_rows,
    write_game_csv,
)
from game.state import initial_state


def test_pos_str_is_column_first() -> None:
    assert pos_to_str((2, 4)) == "4-2"  # row 2, col 4
    assert parse_pos("4-2") == (2, 4)
    assert pos_to_str(None) == "-1"
    assert parse_pos("-1") is None
    for pos in [(0, 0), (3, 1), (10, 12)]:
        assert parse_pos(pos_to_str(pos)) == pos


def test_header_layout() -> None:
    assert games_csv_header(3) == [
        "turn", "player", "score_a", "score_b",
        "card_0", "card_1", "card_2",
        "action", "card_drawn", "src_0", "dst_0", "src_1", "dst_1",
    ]


def _state_with_market(market, positions_a, positions_b, config=None):
    return initial_state(config).with_updates(
        positions={"A": tuple(positions_a), "B": tuple(positions_b)},
        market=market,
    )


def test_action_columns_move() -> None:
    state = _state_with_market((CardType.MOVE1,), [(0, 1), (0, 2), (0, 3)], [(4, 1), (4, 2), (4, 3)])
    action = Action(0, CardType.MOVE1, moves=(PieceMove(0, (1, 1)),))
    cols = action_columns(state, action)
    assert cols == {"action": 0, "src_0": "1-0", "dst_0": "1-1", "src_1": "-1", "dst_1": "-1"}


def test_action_columns_mobilize_full_and_partial() -> None:
    state = _state_with_market((CardType.MOBILIZE,), [(0, 1), (0, 2), (0, 3)], [(4, 1), (4, 2), (4, 3)])
    full = Action(0, CardType.MOBILIZE, moves=(PieceMove(0, (1, 1)), PieceMove(2, (1, 3))))
    cols = action_columns(state, full)
    assert cols == {"action": 0, "src_0": "1-0", "dst_0": "1-1", "src_1": "3-0", "dst_1": "3-1"}
    partial = Action(0, CardType.MOBILIZE, moves=(PieceMove(1, (1, 2)),), mode="partial")
    cols = action_columns(state, partial)
    assert cols == {"action": 0, "src_0": "2-0", "dst_0": "2-1", "src_1": "-1", "dst_1": "-1"}


def test_action_columns_capture_base_and_net() -> None:
    state = _state_with_market((CardType.CAPTURE,), [(2, 1), (2, 2), (0, 0)], [(2, 4), (4, 0), (4, 4)])
    base = Action(0, CardType.CAPTURE, moves=(PieceMove(0, (2, 1)),), target_piece=("B", 1))
    cols = action_columns(state, base)
    assert cols == {"action": 0, "src_0": "1-2", "dst_0": "0-4", "src_1": "-1", "dst_1": "-1"}
    net = Action(0, CardType.CAPTURE, moves=(PieceMove(1, (2, 2)),), target_piece=("B", 0), mode="net", launcher_id=0)
    cols = action_columns(state, net)
    assert cols == {"action": 0, "src_0": "2-2", "dst_0": "4-2", "src_1": "1-2", "dst_1": "-1"}


def test_action_columns_swap() -> None:
    state = _state_with_market((CardType.SWAP,), [(2, 2), (0, 0), (0, 4)], [(3, 3), (4, 0), (4, 4)])
    action = Action(0, CardType.SWAP, moves=(PieceMove(0, (2, 2)),), swap_piece=("B", 0))
    cols = action_columns(state, action)
    assert cols == {"action": 0, "src_0": "2-2", "dst_0": "3-3", "src_1": "-1", "dst_1": "-1"}


def _record_match(config, seed_a=0, seed_b=1):
    initial = initial_state(config)
    recorder = GameCsvRecorder(config.market_size)
    trajectory = [initial]
    def observe(before, action, after):
        recorder.record_step(before, action, after)
        trajectory.append(after)
    result = play_match(RandomAgent(seed=seed_a), RandomAgent(seed=seed_b), initial, on_step=observe)
    return initial, recorder.finalize(), trajectory, result


def _assert_same_trajectory(states, trajectory):
    assert len(states) == len(trajectory)
    for replayed, original in zip(states, trajectory):
        assert replayed.positions == original.positions
        assert replayed.scores == original.scores
        assert replayed.market == original.market
        assert replayed.current_player == original.current_player
        assert replayed.turn_counts == original.turn_counts


def test_full_round_trip_in_memory() -> None:
    config = GameConfig(seed=5, turns_per_player=8)
    initial, rows, trajectory, result = _record_match(config)
    assert len(rows) == 2 * config.turns_per_player + 1
    assert int(rows[-1]["score_a"]) == result.scores["A"]
    assert int(rows[-1]["score_b"]) == result.scores["B"]
    states = replay_rows(initial, rows, validate=True)
    _assert_same_trajectory(states, trajectory)


def test_full_round_trip_through_csv_file(tmp_path) -> None:
    config = GameConfig(seed=9, turns_per_player=6)
    initial, rows, trajectory, _ = _record_match(config)
    path = tmp_path / "game.csv"
    write_game_csv(path, rows, config.market_size)
    states = replay_rows(initial, read_game_csv(path), validate=True)
    _assert_same_trajectory(states, trajectory)


def test_round_trip_across_deck_reshuffles() -> None:
    config = GameConfig(seed=2, turns_per_player=6, deck_composition={CardType.MOVE1: 4})
    initial, rows, trajectory, _ = _record_match(config)
    assert len(rows) == 2 * config.turns_per_player + 1
    states = replay_rows(initial, rows, validate=True)
    _assert_same_trajectory(states, trajectory)


def test_pass_turns_are_recorded_and_replayed() -> None:
    config = GameConfig(seed=1, turns_per_player=2)
    initial = initial_state(config).with_updates(
        positions={"A": ((0, 0), (0, 1), (0, 2)), "B": ((4, 2), (4, 3), (4, 4))},
        market=(CardType.CAPTURE,),
    )
    recorder = GameCsvRecorder(config.market_size)
    play_match(RandomAgent(seed=0), RandomAgent(seed=1), initial, on_step=recorder.record_step)
    rows = recorder.finalize()
    assert len(rows) == 2 * config.turns_per_player + 1
    assert all(int(row["action"]) == -1 for row in rows)
    assert all(row["card_1"] == "None" for row in rows)
    states = replay_rows(initial, rows, validate=True)
    assert states[-1].is_terminal
