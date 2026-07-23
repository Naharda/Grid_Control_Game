"""Golden regression tests locking down default-config behavior.

The values below were captured from the engine at the start of the game-modes
refactor, immediately after the deck-conservation fix (natural draws used to
remove a second copy of the drawn card type from the deck). They guarantee
that a default GameConfig still produces byte-identical games for a given
seed after any refactor.
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
    ("B", ((0, 1), (3, 1), (1, 3)), ((0, 0), (3, 2), (4, 3)), 0, 0, ("capture", "swap", "capture")),
    ("A", ((0, 1), (0, 2), (1, 3)), ((0, 0), (3, 2), (4, 3)), 0, 3, ("move2", "swap", "capture")),
    ("B", ((0, 1), (0, 2), (3, 2)), ((0, 0), (1, 3), (4, 3)), 0, 3, ("move2", "swap", "capture")),
    ("A", ((0, 1), (0, 2), (4, 3)), ((0, 0), (1, 3), (3, 2)), 0, 3, ("move2", "mobilize", "capture")),
]


def test_seeded_random_match_is_reproducible():
    result = play_match(RandomAgent(seed=0), RandomAgent(seed=1), initial_state())
    assert result.winner == "A"
    assert result.scores == {"A": 4, "B": 1}
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


class _ConservationCheckingAgent(RandomAgent):
    def __init__(self, seed, total_cards):
        super().__init__(seed=seed)
        self.total_cards = total_cards

    def choose_action(self, state, legal_actions):
        assert len(state.market) + len(state.deck) + len(state.discard) == self.total_cards
        return super().choose_action(state, legal_actions)


def test_card_count_is_conserved_across_a_full_game():
    total_cards = sum(GameConfig().deck_composition.values())
    result = play_match(
        _ConservationCheckingAgent(seed=3, total_cards=total_cards),
        _ConservationCheckingAgent(seed=4, total_cards=total_cards),
        initial_state(GameConfig(seed=3)),
    )
    assert result.turns == {"A": 50, "B": 50}


def test_initial_market_per_seed():
    expected = {
        0: ("move1", "mobilize", "move2"),
        1: ("capture", "swap", "move2"),
        7: ("move2", "move1", "capture"),
    }
    for seed, market in expected.items():
        state = initial_state(GameConfig(seed=seed))
        assert tuple(card.value for card in state.market) == market
