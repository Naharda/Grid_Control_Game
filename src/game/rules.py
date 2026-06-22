from __future__ import annotations

import random
from collections import Counter
from itertools import combinations, product

from .actions import Action, PieceMove
from .board import ORTHOGONAL_DIRECTIONS, Position, manhattan
from .cards import CardType
from .state import GameState


def other(player: str) -> str:
    return "B" if player == "A" else "A"


def get_legal_actions(state: GameState) -> list[Action]:
    if state.is_terminal:
        return []
    actions: list[Action] = []
    for card_index, card in enumerate(state.market):
        if card == CardType.MOVE1:
            actions.extend(_move_actions(state, card_index, card, 1))
        elif card == CardType.MOVE2:
            actions.extend(_move_actions(state, card_index, card, 2))
        elif card == CardType.MOBILIZE:
            actions.extend(_mobilize_actions(state, card_index, card))
        elif card == CardType.CAPTURE:
            actions.extend(_capture_actions(state, card_index, card))
        elif card == CardType.SWAP:
            actions.extend(_swap_actions(state, card_index, card))
    return actions


def legal_actions_by_card(state: GameState) -> dict[CardType, int]:
    counts = Counter(action.card_type for action in get_legal_actions(state))
    return {card: counts[card] for card in CardType}


def apply_action(state: GameState, action: Action, draw_card: CardType | None = None) -> GameState:
    if action.card_index >= len(state.market) or state.market[action.card_index] != action.card_type:
        raise ValueError("Action does not match the visible market")

    player = state.current_player
    opponent = other(player)
    positions = {p: list(v) for p, v in state.positions.items()}
    scores = dict(state.scores)

    for move in action.moves:
        positions[player][move.piece_id] = move.to_pos

    if action.card_type == CardType.CAPTURE and action.target_piece:
        target_player, target_idx = action.target_piece
        positions[target_player][target_idx] = _return_spawn(state, positions, target_player, target_idx)
        scores[player] += state.config.capture_score

    if action.card_type == CardType.SWAP and action.swap_piece:
        friendly_idx = action.moves[0].piece_id
        target_player, target_idx = action.swap_piece
        positions[player][friendly_idx], positions[target_player][target_idx] = (
            positions[target_player][target_idx],
            positions[player][friendly_idx],
        )

    if state.config.center in positions[player]:
        scores[player] += state.config.center_score

    used_card = state.market[action.card_index]
    market = list(state.market)
    deck = list(state.deck)
    discard = list(state.discard) + [used_card]
    rng = random.Random()
    rng.setstate(state.rng_state)

    if draw_card is None:
        if not deck:
            deck = discard[:]
            discard = []
            rng.shuffle(deck)
        if deck:
            draw_card = deck.pop(0)

    if draw_card is not None:
        if draw_card in deck:
            deck.remove(draw_card)
        elif not deck and draw_card in discard:
            discard.remove(draw_card)
        market[action.card_index] = draw_card
    else:
        market.pop(action.card_index)

    turn_counts = dict(state.turn_counts)
    turn_counts[player] += 1
    return state.with_updates(
        current_player=opponent,
        turn_counts=turn_counts,
        positions={p: tuple(v) for p, v in positions.items()},
        scores=scores,
        market=tuple(market),
        deck=tuple(deck),
        discard=tuple(discard),
        rng_state=rng.getstate(),
        last_action=action.compact(),
    )


def possible_draws(state: GameState, used_card: CardType) -> dict[CardType, float]:
    source = state.deck if state.deck else state.discard + (used_card,)
    counts = Counter(source)
    total = sum(counts.values())
    if total == 0:
        return {}
    return {card: count / total for card, count in counts.items()}


def _move_actions(state: GameState, card_index: int, card: CardType, max_steps: int) -> list[Action]:
    occupied = set(state.occupied())
    actions: list[Action] = []
    for idx, pos in enumerate(state.positions[state.current_player]):
        blocked = occupied - {pos}
        for target in state.board.reachable(pos, max_steps, blocked):
            actions.append(Action(card_index, card, moves=(PieceMove(idx, target),)))
    return actions


def _mobilize_actions(state: GameState, card_index: int, card: CardType) -> list[Action]:
    player = state.current_player
    occupied = set(state.occupied())
    per_piece: dict[int, tuple[Position, ...]] = {}
    for idx, pos in enumerate(state.positions[player]):
        per_piece[idx] = state.board.reachable(pos, 1, occupied - {pos})

    actions: list[Action] = []
    for first, second in combinations(range(len(state.positions[player])), 2):
        for first_target, second_target in product(per_piece[first], per_piece[second]):
            if first_target == second_target:
                continue
            actions.append(
                Action(
                    card_index,
                    card,
                    moves=(PieceMove(first, first_target), PieceMove(second, second_target)),
                )
            )
    if actions:
        return actions

    for idx, targets in per_piece.items():
        for target in targets:
            actions.append(Action(card_index, card, moves=(PieceMove(idx, target),), mode="partial"))
    return actions


def _capture_actions(state: GameState, card_index: int, card: CardType) -> list[Action]:
    player = state.current_player
    enemy = other(player)
    occupied = state.occupied()
    actions: list[Action] = []
    seen: set[tuple[int, int, str]] = set()

    for friendly_idx, friendly_pos in enumerate(state.positions[player]):
        for enemy_idx, enemy_pos in enumerate(state.positions[enemy]):
            if manhattan(friendly_pos, enemy_pos) == 1:
                key = (friendly_idx, enemy_idx, "capture")
                if key not in seen:
                    seen.add(key)
                    actions.append(Action(card_index, card, target_piece=(enemy, enemy_idx)))

    for start, direction in _net_rays(state, player):
        for cell in state.board.ray(start, direction, state.config.net_range):
            occupant = occupied.get(cell)
            if occupant is None:
                continue
            occ_player, occ_idx = occupant
            if occ_player == player:
                break
            key = (start[0] * 10 + start[1], occ_idx, f"net{direction}")
            if key not in seen:
                seen.add(key)
                actions.append(Action(card_index, card, target_piece=(enemy, occ_idx), mode="net"))
            break
    return actions


def _swap_actions(state: GameState, card_index: int, card: CardType) -> list[Action]:
    player = state.current_player
    enemy = other(player)
    actions: list[Action] = []
    for friendly_idx, friendly_pos in enumerate(state.positions[player]):
        for enemy_idx, enemy_pos in enumerate(state.positions[enemy]):
            if manhattan(friendly_pos, enemy_pos) <= state.config.swap_range:
                actions.append(
                    Action(
                        card_index,
                        card,
                        moves=(PieceMove(friendly_idx, friendly_pos),),
                        swap_piece=(enemy, enemy_idx),
                    )
                )
    return actions


def _net_rays(state: GameState, player: str) -> set[tuple[Position, Position]]:
    pieces = state.positions[player]
    rays: set[tuple[Position, Position]] = set()
    for a, b in combinations(pieces, 2):
        if a[0] == b[0]:
            left, right = sorted((a, b), key=lambda p: p[1])
            rays.add((left, (0, -1)))
            rays.add((right, (0, 1)))
        if a[1] == b[1]:
            top, bottom = sorted((a, b), key=lambda p: p[0])
            rays.add((top, (-1, 0)))
            rays.add((bottom, (1, 0)))
    return rays


def _return_spawn(
    state: GameState,
    positions: dict[str, list[Position]],
    player: str,
    captured_idx: int,
) -> Position:
    occupied = {
        pos
        for p, pieces in positions.items()
        for idx, pos in enumerate(pieces)
        if not (p == player and idx == captured_idx)
    }
    spawns = state.config.spawns_for(player)
    for spawn in spawns:
        if spawn not in occupied:
            return spawn
    candidates = sorted(
        (pos for pos in state.board.positions if pos not in occupied),
        key=lambda pos: (min(manhattan(pos, spawn) for spawn in spawns), pos[0], pos[1]),
    )
    if not candidates:
        raise ValueError("No free tile available for captured piece")
    return candidates[0]
