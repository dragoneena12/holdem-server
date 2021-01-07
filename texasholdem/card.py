from functools import total_ordering

import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

BASE_SUIT = list("SHDC")
BASE_NUMBERS = list(range(1, 14))
BASE_PIPS_COURTS = "A23456789TJQK"


@total_ordering
class Card:
    def __init__(self, number: int, suit: str):
        assert 0 <= number <= 13
        assert suit in BASE_SUIT or suit == "B"

        self.number = number
        self.suit = suit

    def __eq__(self, other) -> bool:
        if not isinstance(other, Card):
            return NotImplemented
        return self.number == other.number

    def __lt__(self, other) -> bool:
        if not isinstance(other, Card):
            return NotImplemented
        self_number, other_number = [
            14 if n == 1 else n for n in [self.number, other.number]
        ]
        return self_number < other_number

    def __str__(self):
        return self.to_short_str()

    def __repr__(self):
        return str(self)

    def to_num_str(self):
        return str(self.number) + self.suit

    def to_short_str(self):
        return BASE_PIPS_COURTS[self.number - 1] + self.suit

    def to_dict(self):
        return {"number": self.number, "suit": self.suit}

    def toJSON(self):
        return {"number": self.number, "suit": self.suit}
