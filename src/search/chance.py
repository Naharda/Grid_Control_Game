from __future__ import annotations

import random
from collections import Counter

from game.actions import Action
from game.cards import CardType
from game.rules import apply_action, apply_pass, possible_draws
from game.state import GameState


def public_ordering_successor(state: GameState, action: Action) -> GameState:
    """Return an order-invariant successor for action ranking.

    The most probable public draw is used; ties are resolved by card name.
    Search values still handle chance separately. This helper exists only to
    prevent beam ordering and baseline tie-breaking from reading deck order.
    """
    draws = possible_draws(state, action.card_type)
    if not draws:
        return apply_action(state, action)
    card = min(draws, key=lambda item: (-draws[item], item.value))
    return apply_action(state, action, draw_card=card)


def sample_action_successor(state: GameState, action: Action, rng: random.Random) -> GameState:
    draws = possible_draws(state, action.card_type)
    if not draws:
        return apply_action(state, action)
    return apply_action(state, action, draw_card=_sample_distribution(draws, rng))


def sample_pass_successor(state: GameState, rng: random.Random) -> GameState:
    threshold = state.config.market_refresh_after_passes
    if threshold is None or state.consecutive_passes + 1 < threshold:
        return apply_pass(state)

    deck = list(state.deck)
    discard = list(state.discard) + list(state.market)
    draws: list[CardType] = []
    for _ in range(state.config.market_size):
        source = deck if deck else discard
        if not source:
            break
        card = _sample_counts(source, rng)
        source.remove(card)
        draws.append(card)
    return apply_pass(state, draw_cards=tuple(draws))


def public_state_key(state: GameState) -> tuple:
    """Hash a simulated state by public facts and unordered card counts."""
    deck_counts = tuple(sorted((card.value, count) for card, count in Counter(state.deck).items()))
    discard_counts = tuple(sorted((card.value, count) for card, count in Counter(state.discard).items()))
    return state.as_hashable(include_deck=False) + (deck_counts, discard_counts)


def _sample_counts(cards: list[CardType] | tuple[CardType, ...], rng: random.Random) -> CardType:
    counts = Counter(cards)
    total = sum(counts.values())
    draw = rng.randrange(total)
    cumulative = 0
    for card in sorted(counts, key=lambda item: item.value):
        cumulative += counts[card]
        if draw < cumulative:
            return card
    raise AssertionError("unreachable weighted draw")


def _sample_distribution(draws: dict[CardType, float], rng: random.Random) -> CardType:
    threshold = rng.random()
    cumulative = 0.0
    ordered = sorted(draws, key=lambda item: item.value)
    for card in ordered:
        cumulative += draws[card]
        if threshold <= cumulative:
            return card
    return ordered[-1]
