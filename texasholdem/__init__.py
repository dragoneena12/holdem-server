from texasholdem.player import Player
from texasholdem.table import Table
from texasholdem.card import Card
from texasholdem.deck import Deck
from texasholdem.error import (
    NotEnoughPlayerError,
    NotEnoughPlayerBankrollError,
    PlayerLimitExceededError,
    OutOfBuyInRangeError,
    OccupiedSeatError,
)

import json


class SasakiJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        print(obj)
        if hasattr(obj, "toJSON") and callable(obj.toJSON):
            return obj.toJSON()
        return json.JSONEncoder.default(self, obj)
