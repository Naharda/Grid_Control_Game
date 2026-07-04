"""Golden regression tests locking down default-config behavior.

The values below were captured from the engine before the game-modes refactor
(branch point: master @ d33b83d). They guarantee that a default GameConfig
still produces byte-identical games for a given seed after any refactor.
"""

from agents.random_agent import RandomAgent
from game.config import GameConfig
from game.engine import play_match
from game.rules import apply_action, get_legal_actions
from game.state import initial_state

GOLDEN_TRAJECTORY = [
    ("B", ((1, 0), (0, 2), (0, 3)), ((4, 1), (4, 2), (4, 3)), 0, 0, ("move2", "move1", "capture")),
    ("A", ((1, 0), (0, 2), (0, 3)), ((3, 1), (4, 2), (4, 3)), 0, 0, ("move1", "move1", "capture")),
    ("B", ((1, 0), (0, 1), (0, 3)), ((3, 1), (4, 2), (4, 3)), 0, 0, ("move1", "swap", "capture")),
    ("A", ((1, 0), (0, 1), (0, 3)), ((3, 1), (3, 2), (4, 3)), 0, 0, ("mobilize", "swap", "capture")),
    ("B", ((0, 0), (0, 1), (1, 3)), ((3, 1), (3, 2), (4, 3)), 0, 0, ("capture", "swap", "capture")),
    ("A", ((0, 0), (3, 1), (1, 3)), ((0, 1), (3, 2), (4, 3)), 0, 0, ("capture", "swap", "capture")),
    ("B", ((0, 1), (3, 1), (1, 3)), ((0, 0), (3, 2), (4, 3)), 0, 0, ("capture", "move1", "capture")),
    ("A", ((0, 1), (0, 2), (1, 3)), ((0, 0), (3, 2), (4, 3)), 0, 3, ("mobilize", "move1", "capture")),
    ("B", ((0, 1), (0, 2), (1, 2)), ((0, 0), (3, 2), (4, 3)), 0, 3, ("mobilize", "capture", "capture")),
    ("A", ((0, 1), (0, 2), (1, 2)), ((1, 0), (3, 1), (4, 3)), 0, 3, ("move2", "capture", "capture")),
]


def test_seeded_random_match_is_reproducible():
    result = play_match(RandomAgent(seed=0), RandomAgent(seed=1), initial_state())
    assert result.winner == "B"
    assert result.scores == {"A": 22, "B": 25}
    assert result.turns == {"A": 50, "B": 50}


def test_seeded_trajectory_is_reproducible():
    state = initial_state(GameConfig(seed=7))
    agent = RandomAgent(seed=42)
    for expected in GOLDEN_TRAJECTORY:
        action = agent.choose_action(state, get_legal_actions(state))
        state = apply_action(state, action)
        observed = (
            state.current_player,
            tuple(state.positions["A"]),
            tuple(state.positions["B"]),
            state.scores["A"],
            state.scores["B"],
            tuple(card.value for card in state.market),
        )
        assert observed == expected


def test_initial_market_per_seed():
    expected = {
        0: ("move1", "mobilize", "move2"),
        1: ("capture", "swap", "move2"),
        7: ("move2", "move1", "capture"),
    }
    for seed, market in expected.items():
        state = initial_state(GameConfig(seed=seed))
        assert tuple(card.value for card in state.market) == market
