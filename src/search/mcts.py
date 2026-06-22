from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

from game.actions import Action
from game.rules import apply_action, get_legal_actions
from game.state import GameState
from search.heuristic import evaluate_state


@dataclass
class MCTSNode:
    state: GameState
    parent: "MCTSNode | None" = None
    action: Action | None = None
    children: list["MCTSNode"] = field(default_factory=list)
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
    rng = random.Random(seed)
    root = MCTSNode(state=state, untried=get_legal_actions(state))
    if not root.untried:
        raise ValueError("No legal actions")

    for _ in range(simulations):
        node = root
        while not node.untried and node.children:
            node = _select_child(node, exploration)
        if node.untried:
            action = node.untried.pop(rng.randrange(len(node.untried)))
            child_state = apply_action(node.state, action)
            child = MCTSNode(state=child_state, parent=node, action=action, untried=get_legal_actions(child_state))
            node.children.append(child)
            node = child
        reward = _rollout(node.state, player, rollout_depth, rng)
        while node is not None:
            node.visits += 1
            node.value += reward
            node = node.parent

    return max(root.children, key=lambda child: child.visits).action  # type: ignore[return-value]


def _select_child(node: MCTSNode, exploration: float) -> MCTSNode:
    log_parent = math.log(max(1, node.visits))
    return max(
        node.children,
        key=lambda child: child.value / max(1, child.visits)
        + exploration * math.sqrt(log_parent / max(1, child.visits)),
    )


def _rollout(state: GameState, player: str, depth: int, rng: random.Random) -> float:
    cur = state
    for _ in range(depth):
        if cur.is_terminal:
            break
        legal = get_legal_actions(cur)
        if not legal:
            break
        cur = apply_action(cur, rng.choice(legal))
    return evaluate_state(cur, player)
