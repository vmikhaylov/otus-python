#!/usr/bin/env python
# -*- coding: utf-8 -*-

# -----------------
# Реализуйте функцию best_hand, которая принимает на вход
# покерную "руку" (hand) из 7ми карт и возвращает лучшую
# (относительно значения, возвращаемого hand_rank)
# "руку" из 5ти карт. У каждой карты есть масть(suit) и
# ранг(rank)
# Масти: трефы(clubs, C), пики(spades, S), червы(hearts, H), бубны(diamonds, D)
# Ранги: 2, 3, 4, 5, 6, 7, 8, 9, 10 (ten, T), валет (jack, J), дама (queen, Q), король (king, K), туз (ace, A)
# Например: AS - туз пик (ace of spades), TH - дестяка черв (ten of hearts), 3C - тройка треф (three of clubs)

# Задание со *
# Реализуйте функцию best_wild_hand, которая принимает на вход
# покерную "руку" (hand) из 7ми карт и возвращает лучшую
# (относительно значения, возвращаемого hand_rank)
# "руку" из 5ти карт. Кроме прочего в данном варианте "рука"
# может включать джокера. Джокеры могут заменить карту любой
# масти и ранга того же цвета. Черный джокер '?B' может быть
# использован в качестве треф или пик любого ранга, красный
# джокер '?R' - в качестве черв и бубен люього ранга.

# Одна функция уже реализована, сигнатуры и описания других даны.
# Вам наверняка пригодится itertools
# Можно свободно определять свои функции и т.п.
# -----------------

import collections
import itertools

TO_RANKS_MAP = {rank_str: rank
                for rank, rank_str in enumerate('0123456789TJQKA')}
FROM_RANKS_MAP = {rank: rank_str for rank_str, rank in TO_RANKS_MAP.iteritems()}


Card = collections.namedtuple('Card', ['rank', 'suit'])


class TooManyJokers(RuntimeError):
    """Во входной руке более 2-х джокеров"""


class Joker:
    def all_cards(self):
        return [Card(rank=rank, suit=suit)
                for rank in FROM_RANKS_MAP
                for suit in self.suits]


class RedJoker(Joker):
    card_str = '?R'
    suits = ('H', 'D')


class BlackJoker(Joker):
    card_str = '?B'
    suits = ('S', 'C')


def hand_rank(hand):
    """Возвращает значение определяющее ранг 'руки'"""
    ranks = card_ranks(hand)
    if straight(ranks) and flush(hand):
        return (8, max(ranks))
    elif kind(4, ranks):
        return (7, kind(4, ranks), kind(1, ranks))
    elif kind(3, ranks) and kind(2, ranks):
        return (6, kind(3, ranks), kind(2, ranks))
    elif flush(hand):
        return (5, ranks)
    elif straight(ranks):
        return (4, max(ranks))
    elif kind(3, ranks):
        return (3, kind(3, ranks), ranks)
    elif two_pair(ranks):
        return (2, two_pair(ranks), ranks)
    elif kind(2, ranks):
        return (1, kind(2, ranks), ranks)
    else:
        return (0, ranks)


def card_ranks(hand):
    """Возвращает список рангов, отсортированный от большего к меньшему"""
    return sorted((card.rank for card in hand), reverse=True)


def flush(hand):
    """Возвращает True, если все карты одной масти"""
    return len(set(card.suit for card in hand)) <= 1


def straight(ranks):
    """Возвращает True, если отсортированные ранги формируют последовательность 5ти,
    где у 5ти карт ранги идут по порядку (стрит)"""
    good_orders = [ranks[i] - 1 == ranks[i + 1]
                   for i in xrange(len(ranks) - 1)]
    return any(ordered and len(list(group)) >= 4
               for ordered, group in itertools.groupby(good_orders))


def kind(n, ranks):
    """Возвращает первый ранг, который n раз встречается в данной руке.
    Возвращает None, если ничего не найдено"""
    for rank, group in itertools.groupby(ranks):
        rank_cnt = len(list(group))
        if rank_cnt == n:
            return rank
    return None


def two_pair(ranks):
    """Если есть две пары, то возврщает два соответствующих ранга,
    иначе возвращает None"""
    pairs = []
    for rank, group in itertools.groupby(ranks):
        if len(list(group)) == 2:
            pairs.append(rank)
            if len(pairs) == 2:
                return pairs
    return None


def best_hand(hand):
    """Из "руки" в 7 карт возвращает лучшую "руку" в 5 карт """
    cards = [Card(rank=TO_RANKS_MAP[card_str[0]], suit=card_str[1])
             for card_str in hand]
    max_rank_cards = _best_hand(cards)
    return ['%s%s' % (FROM_RANKS_MAP[card.rank], card.suit)
            for card in max_rank_cards]


def best_wild_hand(hand):
    """best_hand но с джокерами"""
    jokers = []
    cards = []
    for card_str in hand:
        if card_str == BlackJoker.card_str:
            jokers.append(BlackJoker())
        elif card_str == RedJoker.card_str:
            jokers.append(RedJoker())
        else:
            cards.append(
                Card(rank=TO_RANKS_MAP[card_str[0]], suit=card_str[1])
            )

    max_rank = None
    max_rank_cards = None
    if len(jokers) == 0:
        max_rank_cards = _best_hand(cards)
    elif len(jokers) == 1:
        for guess_card in jokers[0].all_cards():
            if guess_card in cards:
                continue
            cards.append(guess_card)
            cur_max_rank_cards = _best_hand(cards)
            cur_max_rank = hand_rank(cur_max_rank_cards)
            if not max_rank_cards or cur_max_rank > max_rank:
                max_rank_cards = cur_max_rank_cards
                max_rank = cur_max_rank
            cards.pop()
    elif len(jokers) == 2:
        for guess_cards in itertools.product(
                jokers[0].all_cards(), jokers[1].all_cards()):
            if any(guess_card in cards for guess_card in guess_cards):
                continue
            cards.extend(guess_cards)
            cur_max_rank_cards = _best_hand(cards)
            cur_max_rank = hand_rank(cur_max_rank_cards)
            if not max_rank_cards or cur_max_rank > max_rank:
                max_rank_cards = cur_max_rank_cards
                max_rank = cur_max_rank
            for _ in guess_cards:
                cards.pop()
    else:
        raise TooManyJokers()

    return ['%s%s' % (FROM_RANKS_MAP[card.rank], card.suit)
            for card in max_rank_cards]


def _best_hand(cards):
    """Возвращает лучшую руку для iterable из кортежей Card"""
    return max(itertools.combinations(cards, 5),
               key=lambda combination: hand_rank(combination))


def test_best_hand():
    print "test_best_hand..."
    assert (sorted(best_hand("6C 7C 8C 9C TC 5C JS".split()))
            == ['6C', '7C', '8C', '9C', 'TC'])
    assert (sorted(best_hand("TD TC TH 7C 7D 8C 8S".split()))
            == ['8C', '8S', 'TC', 'TD', 'TH'])
    assert (sorted(best_hand("JD TC TH 7C 7D 7S 7H".split()))
            == ['7C', '7D', '7H', '7S', 'JD'])
    print 'OK'


def test_best_wild_hand():
    print "test_best_wild_hand..."
    assert (sorted(best_wild_hand("6C 7C 8C 9C TC 5C ?B".split()))
            == ['7C', '8C', '9C', 'JC', 'TC'])
    assert (sorted(best_wild_hand("TD TC 5H 5C 7C ?R ?B".split()))
            == ['7C', 'TC', 'TD', 'TH', 'TS'])
    assert (sorted(best_wild_hand("JD TC TH 7C 7D 7S 7H".split()))
            == ['7C', '7D', '7H', '7S', 'JD'])
    print 'OK'


if __name__ == '__main__':
    test_best_hand()
    test_best_wild_hand()
