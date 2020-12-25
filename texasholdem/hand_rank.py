from __future__ import annotations
from typing import List
from texasholdem import Card, Deck

import enum
import logging

from texasholdem.card import BASE_SUIT, BASE_NUMBERS

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


RANK_ORDER = [
    "royal_flush",
    "straight_flush",
    "four_of_a_kind",
    "full_house",
    "flush",
    "straight",
    "three_of_a_kind",
    "two_pair",
    "one_pair",
    "high_card",
]


class RankName(enum.Enum):
    royal_flush = 10
    straight_flush = 9
    four_of_a_kind = 8
    full_house = 7
    flush = 6
    straight = 5
    three_of_a_kind = 4
    two_pair = 3
    one_pair = 2
    high_card = 1


class HandRank:
    def __init__(self, cards: List[Card] = None):
        if len(cards) < 5:
            logger.error("cards is not enough!")
            return
        else:
            self.rank_name = RankName.high_card
            self.rank_number = [7, 6, 5, 4, 2]
            self.kicker = []

    def get_rank(self, cards: List[Card]):
        if len(cards) != 5:
            logger.error("cannot call get_rank with other than 5 cards!")
            return
        number_count = [0 for c in range(14)]
        suit_count = {}
        for c in cards:
            number_count[c.number] += 1
            if c.number == 1:
                number_count[14] += 1
            if c.suit in suit_count:
                suit_count[c.suit] += 1
            else:
                suit_count[c.suit] = 1
        self.rank_name = RankName.high_card
        for i in range(2, 15):
            if number_count(i) == 2:
                if self.rank_name == RankName.high_card:
                    self.rank_name = RankName.one_pair
                    self.rank_number.append(i)
                elif self.rank_name == RankName.one_pair:
                    self.rank_name = RankName.two_pair
                    self.rank_number.insert(0, i)
                elif self.rank_name == RankName.three_of_a_kind:
                    self.rank_name = RankName.full_house
                    self.rank_number.append(i)

        if max(number_count) >= 2:
            self.rank = RankName.one_pair
        if len(v for v in number_count if number_count >= 2) >= 2:
            self.rank = RankName.two_pair
        if max(number_count) >= 3:
            self.rank = RankName.three_of_a_kind

    def to_dict(self):
        return {"rank": self.rank, "kicker": self.kicker.to_dict()}

    def __eq__(self, other: HandRank):
        if not isinstance(other, HandRank):
            return NotImplemented
        return self.rank == other.rank and self.kicker == other.kicker

    def __lt__(self, other):
        if not isinstance(other, HandRank):
            return NotImplemented
        return self.rank < other.rank or (
            self.rank == other.rank and self.kicker < other.kicker
        )

    def __str__(self) -> str:
        return str(self.rank)


if __name__ == "__main__":
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
