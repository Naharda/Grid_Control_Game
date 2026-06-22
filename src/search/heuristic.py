from __future__ import annotations

from game.board import manhattan
from game.cards import CardType
from game.rules import get_legal_actions, other
from game.state import GameState


def evaluate_state(state: GameState, player: str, weights: dict[str, float] | None = None) -> float:
    weights = weights or state.config.heuristic_weights
    opponent = other(player)
    score_diff = state.scores[player] - state.scores[opponent]
    center = state.config.center
    my_positions = state.positions[player]
    opp_positions = state.positions[opponent]

    center_control = int(center in my_positions) - int(center in opp_positions)
    center_distance = sum(manhattan(p, center) for p in opp_positions) - sum(
        manhattan(p, center) for p in my_positions
    )
    capture_threat = _capture_threats(state, player) - _capture_threats(state, opponent)
    net_potential = _net_potential(state, player) - _net_potential(state, opponent)
    swap_potential = _swap_potential(state, player) - _swap_potential(state, opponent)
    safety = _piece_safety(state, player) - _piece_safety(state, opponent)
    mobility = _mobility(state, player) - _mobility(state, opponent)

    return (
        weights["score"] * score_diff
        + weights["center"] * center_control
        + weights["center_distance"] * center_distance
        + weights["capture_threat"] * capture_threat
        + weights["net_potential"] * net_potential
        + weights["swap_potential"] * swap_potential
        + weights["safety"] * safety
        + weights["mobility"] * mobility
    )


def _capture_threats(state: GameState, player: str) -> int:
    opponent = other(player)
    threats = 0
    for a in state.positions[player]:
        for b in state.positions[opponent]:
            if manhattan(a, b) == 1:
                threats += 1
    for a in state.positions[player]:
        for b in state.positions[player]:
            if a >= b:
                continue
            aligned = a[0] == b[0] or a[1] == b[1]
            if not aligned:
                continue
            for enemy in state.positions[opponent]:
                if (enemy[0] == a[0] == b[0] or enemy[1] == a[1] == b[1]) and min(
                    manhattan(enemy, a), manhattan(enemy, b)
                ) <= state.config.net_range:
                    threats += 1
    return threats


def _net_potential(state: GameState, player: str) -> int:
    pieces = state.positions[player]
    aligned = sum(1 for i, a in enumerate(pieces) for b in pieces[i + 1 :] if a[0] == b[0] or a[1] == b[1])
    near_alignment = 0
    for i, a in enumerate(pieces):
        for b in pieces[i + 1 :]:
            if abs(a[0] - b[0]) == 1 or abs(a[1] - b[1]) == 1:
                near_alignment += 1
    return aligned * 2 + near_alignment


def _swap_potential(state: GameState, player: str) -> int:
    opponent = other(player)
    center = state.config.center
    value = 0
    for friendly in state.positions[player]:
        for enemy in state.positions[opponent]:
            if manhattan(friendly, enemy) <= state.config.swap_range:
                if enemy == center:
                    value += 3
                if friendly == center:
                    value -= 1
                value += 1
    return value


def _piece_safety(state: GameState, player: str) -> int:
    opponent = other(player)
    unsafe = 0
    for piece in state.positions[player]:
        for enemy in state.positions[opponent]:
            if manhattan(piece, enemy) == 1:
                unsafe += 1
    return -unsafe


def _mobility(state: GameState, player: str) -> int:
    if state.current_player == player:
        return len(get_legal_actions(state))
    proxy = state.with_updates(current_player=player)
    return len(get_legal_actions(proxy))


def action_priority(state: GameState, action_card: CardType) -> int:
    priorities = {
        CardType.CAPTURE: 4,
        CardType.SWAP: 3,
        CardType.MOBILIZE: 2,
        CardType.MOVE2: 1,
        CardType.MOVE1: 0,
    }
    return priorities[action_card]
