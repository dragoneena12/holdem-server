from __future__ import annotations
from typing import List, Union
from texasholdem import Card

import logging

from texasholdem.card import BASE_SUIT, BASE_NUMBERS

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class Deck:
    def __init__(self, cards=None):
        from itertools import product
        if cards is None:
            self.cards = [Card(n, s) for n, s in product(BASE_NUMBERS, BASE_SUIT)]
        else:
            self.cards = cards

    def shuffle(self, seed=None):
        import random
        random.seed(seed)
        random.shuffle(self.cards)

    def peek(self, num=1) -> __class__:
        assert 1 <= num <= len(self.cards)

        return Deck(self.cards[0:num])

    def draw(self, num=1) -> __class__:
        assert 1 <= num <= len(self.cards)
        drawn_cards, self.cards = Deck(self.cards[0:num]), self.cards[num:]
        return drawn_cards

    def to_dict_list(self):
        return [c.to_dict() for c in self.cards]

    def __str__(self) -> str:
        return str(self.cards)

    def __getitem__(self, item) -> Union[Card, List[Card]]:
        if isinstance(item, slice):
            return self.cards[item]
        if isinstance(item, int):
            return self.cards[item]
        raise NotImplemented


if __name__ == '__main__':
    logger.debug("BASE_SUIT: {}".format(BASE_SUIT))
    logger.debug("BASE_NUMBERS: {}".format(BASE_NUMBERS))
    deck = Deck()
    logger.debug("Original Cards: {}".format(deck))
    deck.shuffle()
    logger.debug("Shuffled Cards: {}".format(deck))
    draw = deck.draw(1)
    logger.debug("Drawn: {}, Deck:{}".format(draw, deck))
    draw = deck.draw(2)
    logger.debug("Drawn: {}, Deck:{}".format(draw, deck))
