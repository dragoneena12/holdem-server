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


class HandRank5:
    def __init__(self, cards: List[Card] = None):
        if len(cards) != 5:
            logger.error("cannot initialize HandRank5 with other than 5 cards")
            return
        else:
            self.rank_name, self.rank_number, self.kicker = self.get_rank(cards)

    def get_rank(self, cards: List[Card]):
        if len(cards) != 5:
            logger.error("cannot call get_rank with other than 5 cards")
            raise Exception
        number_count = [0 for c in range(14)]
        suit_count = {}
        isStraight = False
        isFlush = False
        rank_name = RankName.high_card
        rank_number = []
        kicker = []
        for c in cards:
            number_count[c.number] += 1
            if c.number == 1:
                number_count[14] += 1
            if c.suit in suit_count:
                suit_count[c.suit] += 1
            else:
                suit_count[c.suit] = 1
        rank_name = RankName.high_card
        # pair系hand判定
        for i in range(2, 15):
            if number_count(i) == 1:
                kicker.insert(0, i)
            elif number_count(i) == 2:
                if rank_name == RankName.high_card:
                    rank_name = RankName.one_pair
                    rank_number.insert(0, i)
                elif rank_name == RankName.one_pair:
                    rank_name = RankName.two_pair
                    rank_number.insert(0, i)
                elif rank_name == RankName.three_of_a_kind:
                    rank_name = RankName.full_house
                    rank_number.append(i)
            elif number_count(i) == 3:
                if rank_name == RankName.high_card:
                    rank_name = RankName.three_of_a_kind
                    rank_number.insert(0, i)
                elif rank_name == RankName.one_pair:
                    rank_name = RankName.full_house
                    rank_number.insert(0, i)
            elif number_count(i) == 4:
                rank_name = RankName.four_of_a_kind
                rank_number.insert(0, i)
        # Straight判定
        for i in range(1, 11):
            flag = True
            for j in range(5):
                if number_count(i + j) != 1:
                    flag = False
            if flag:
                isStraight = True
        # Flush判定
        for i, v in suit_count.items():
            if v == 5:
                isFlush = True
        # 役判定
        if isStraight and isFlush:
            rank_name = RankName.straight_flush
        if isStraight and rank_name < RankName.straight:
            rank_name = RankName.straight
        if isFlush and rank_name < RankName.flush:
            rank_name = RankName.flush
        return (rank_name, rank_number, kicker)

    def to_dict(self):
        return {"rank": self.rank, "kicker": self.kicker.to_dict()}

    def __eq__(self, other: HandRank5):
        if not isinstance(other, HandRank5):
            return NotImplemented
        return (
            self.rank_name == other.rank_name
            and self.rank_number == other.rank_number
            and self.kicker == other.kicker
        )

    def __lt__(self, other):
        if not isinstance(other, HandRank5):
            return NotImplemented
        return self.rank_name < other.rank_name or (
            self.rank_name == other.rank_name and self.kicker < other.kicker
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
