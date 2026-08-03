from __future__ import annotations

from agents.greedy_agent import GreedyAgent
from agents.mcts_agent import MCTSAgent
from agents.rule_based_agent import RuleBasedAgent
from agents.search_agent import SearchAgent
from game.rules import get_legal_actions
from game.state import initial_state
from search.chance import public_ordering_successor
from search.expectimax import _ordered_actions
from search.heuristic import evaluate_state
from search.mcts import MCTSActionEdge, MCTSNode, _select_edge


def _deck_orders():
    state = initial_state()
    return state, state.with_updates(deck=tuple(reversed(state.deck)))


def test_public_information_agents_ignore_hidden_deck_order() -> None:
    first, reversed_deck = _deck_orders()
    agents = [
        GreedyAgent(),
        RuleBasedAgent(),
        SearchAgent(method="expectimax", depth=2, top_k=2),
        MCTSAgent(simulations=80, rollout_depth=8, seed=17),
    ]
    for agent in agents:
        action_a = agent.choose_action(first, get_legal_actions(first))
        action_b = agent.choose_action(reversed_deck, get_legal_actions(reversed_deck))
        assert action_a == action_b, type(agent).__name__


def test_expectimax_beam_orders_opponent_actions_adversarially() -> None:
    state = initial_state().with_updates(current_player="B")
    actions = get_legal_actions(state)
    ordered = _ordered_actions(state, actions, player="A", top_k=1)
    values = [evaluate_state(public_ordering_successor(state, action), "A") for action in actions]
    assert evaluate_state(public_ordering_successor(state, ordered[0]), "A") == min(values)


def test_mcts_selection_minimizes_at_opponent_node() -> None:
    state = initial_state().with_updates(current_player="B")
    actions = get_legal_actions(state)
    low = MCTSActionEdge(actions[0], visits=10, value=-50.0)
    high = MCTSActionEdge(actions[1], visits=10, value=50.0)
    node = MCTSNode(state=state, edges=[high, low], visits=20)
    assert _select_edge(node, exploration=0.0, player="A") is low


def test_mcts_selection_maximizes_at_root_player_node() -> None:
    state = initial_state()
    actions = get_legal_actions(state)
    low = MCTSActionEdge(actions[0], visits=10, value=-50.0)
    high = MCTSActionEdge(actions[1], visits=10, value=50.0)
    node = MCTSNode(state=state, edges=[low, high], visits=20)
    assert _select_edge(node, exploration=0.0, player="A") is high
