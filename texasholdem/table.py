from functools import reduce

from texasholdem import Player, Deck
from typing import List, Dict

import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class Table:
    def __init__(self, players_limit: int):
        self.id = id(self)  # 仮
        self.isInitialized = False
        self.stakes = {
            "SB": 1,
            "BB": 2,
            "ante": 0,
        }
        self.players_limit = players_limit
        self.player_num = 0
        self.player_seating_chart = [None for _ in range(players_limit)]
        self.hands = {}
        self.board = []
        self.seated_players = []
        self.betting = [0 for _ in range(players_limit)]
        self.player_ongoing = [False for _ in range(players_limit)]
        self.played = [False for _ in range(players_limit)]
        self.current_betting_amount = 0
        self.current_pot_size = 0
        self.player_status = {}  # type: Dict[Player, Dict]
        self.status = "beforeGame"
        self.button_player = 0
        self.current_player = 0  # 0 = button
        self.deck = Deck()

    def __eq__(self, other):
        if not isinstance(other, Table):
            return False
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)

    def __change_stakes(self, sb: int, bb: int, ante=0):
        self.stakes = {"SB": sb, "BB": bb, "ante": ante}

    def next_player(self):
        cp = self.current_player
        cp = (cp + 1) % self.players_limit
        while not self.player_ongoing[cp]:
            cp = (cp + 1) % self.players_limit
        logger.debug("next player is {} !".format(cp))
        self.current_player = cp

    def bet(self, player_seat: int, amount: int):
        if not self.player_seating_chart[player_seat].pay(
            amount - self.betting[player_seat]
        ):
            logger.debug("state: {}".format("Bankroll in not enough."))
            raise Exception("Bankroll in not enough.")  # TODO: いい感じの例外クラスを作る
        self.betting[player_seat] = amount
        logger.debug(
            "betting: player_seat = {}, amount = {}".format(player_seat, amount)
        )

    def is_round_over(self):
        logger.debug("checking is_round_over...")
        # そもそも参加者がいない場合
        if reduce(
            lambda a, b: a and b,
            list(
                map(
                    lambda x: not self.player_ongoing[x],
                    range(self.players_limit),
                )
            ),
        ):
            return False
        return reduce(
            lambda a, b: a and b,
            list(
                map(
                    lambda x: not self.player_ongoing[x] or self.played[x],
                    range(self.players_limit),
                )
            ),
        )

    def next_round(self):
        self.current_pot_size += reduce(lambda a, b: a + b, self.betting)
        self.betting = [0 for _ in self.betting]
        self.played = [False for _ in self.played]
        self.current_betting_amount = 0
        self.current_player = self.button_player
        self.next_player()