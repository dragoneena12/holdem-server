from typing import List

from texasholdem import Card

import logging

from texasholdem.card import BASE_SUIT, BASE_NUMBERS

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class Deck:
    def __init__(self):
        from itertools import product
        self.cards = [Card(n, s) for n, s in product(BASE_NUMBERS, BASE_SUIT)]

    def shuffle(self, seed=None):
        import random
        random.seed(seed)
        random.shuffle(self.cards)

    def peek(self, num=1) -> List[Card]:
        assert 1 <= num <= len(self.cards)

        return self.cards[0:num]

    def draw(self, num=1) -> List[Card]:
        assert 1 <= num <= len(self.cards)
        drawn_cards, self.cards = self.cards[0:num], self.cards[num:]
        return drawn_cards

    def __str__(self) -> str:
        return str(self.cards)


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
