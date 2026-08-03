from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

from game.actions import Action
from game.rules import get_legal_actions
from game.state import GameState
from search.chance import public_state_key, sample_action_successor, sample_pass_successor
from search.heuristic import evaluate_state


@dataclass
class MCTSActionEdge:
    action: Action
    outcomes: dict[tuple, "MCTSNode"] = field(default_factory=dict)
    visits: int = 0
    value: float = 0.0


@dataclass
class MCTSNode:
    state: GameState
    edges: list[MCTSActionEdge] = field(default_factory=list)
    untried: list[Action] = field(default_factory=list)
    visits: int = 0
    value: float = 0.0


def choose_mcts(
    state: GameState,
    player: str,
    simulations: int = 200,
    rollout_depth: int = 20,
    exploration: float = 1.4,
    seed: int | None = None,
) -> Action:
    """Sample public chance outcomes and model both players' decisions.

    Action-edge statistics aggregate multiple sampled chance outcomes. The
    match's ordered deck and RNG state are never used to choose a simulated
    refill. Opponent nodes minimize root-player value while retaining an
    exploration incentive for under-sampled actions.
    """
    rng = random.Random(seed)
    root = _new_node(state)
    if not root.untried:
        raise ValueError("No legal actions")

    for _ in range(simulations):
        node = root
        path_nodes = [node]
        path_edges: list[MCTSActionEdge] = []

        while not node.state.is_terminal:
            if not node.untried and not node.edges:
                break

            if node.untried:
                action = node.untried.pop(rng.randrange(len(node.untried)))
                edge = MCTSActionEdge(action=action)
                node.edges.append(edge)
                child, _ = _sample_outcome(node.state, edge, rng)
                path_edges.append(edge)
                path_nodes.append(child)
                node = child
                break

            edge = _select_edge(node, exploration, player)
            child, created = _sample_outcome(node.state, edge, rng)
            path_edges.append(edge)
            path_nodes.append(child)
            node = child
            if created:
                break

        reward = _rollout(node.state, player, rollout_depth, rng)
        for visited in path_nodes:
            visited.visits += 1
            visited.value += reward
        for edge in path_edges:
            edge.visits += 1
            edge.value += reward

    return max(root.edges, key=lambda edge: edge.visits).action


def _new_node(state: GameState) -> MCTSNode:
    return MCTSNode(state=state, untried=get_legal_actions(state))


def _sample_outcome(
    state: GameState,
    edge: MCTSActionEdge,
    rng: random.Random,
) -> tuple[MCTSNode, bool]:
    successor = sample_action_successor(state, edge.action, rng)
    key = public_state_key(successor)
    child = edge.outcomes.get(key)
    if child is not None:
        return child, False
    child = _new_node(successor)
    edge.outcomes[key] = child
    return child, True


def _select_edge(node: MCTSNode, exploration: float, player: str) -> MCTSActionEdge:
    log_parent = math.log(max(1, node.visits))

    def mean(edge: MCTSActionEdge) -> float:
        return edge.value / max(1, edge.visits)

    def bonus(edge: MCTSActionEdge) -> float:
        return exploration * math.sqrt(log_parent / max(1, edge.visits))

    if node.state.current_player == player:
        return max(node.edges, key=lambda edge: mean(edge) + bonus(edge))
    return min(node.edges, key=lambda edge: mean(edge) - bonus(edge))


def _rollout(state: GameState, player: str, depth: int, rng: random.Random) -> float:
    cur = state
    for _ in range(depth):
        if cur.is_terminal:
            break
        legal = get_legal_actions(cur)
        if legal:
            cur = sample_action_successor(cur, rng.choice(legal), rng)
        else:
            cur = sample_pass_successor(cur, rng)
    return evaluate_state(cur, player)
