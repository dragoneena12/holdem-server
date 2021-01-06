from functools import reduce

from texasholdem import Player, Deck, Card, HandRank
from typing import Dict, List

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
        self.player_seating_chart = [
            None for _ in range(players_limit)
        ]  # type: List[Player]
        self.hands = {}  # type: Dict[str, List[Card]]
        self.hand_ranks = {}  # type: Dict[str, HandRank]
        self.board = []
        self.betting = [0 for _ in range(players_limit)]
        self.player_ongoing = [False for _ in range(players_limit)]
        self.played = [False for _ in range(players_limit)]
        self.showdown_hands = [
            None for _ in range(players_limit)
        ]  # type: List[List[Card]]
        self.current_betting_amount = 0
        self.current_pot_size = 0
        self.status = "beforeGame"
        self.button_player = 0
        self.current_player = -1  # 0 = button
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
            # raise Exception("Bankroll in not enough.") TODO: いい感じの例外クラスを作る
            return False
        self.betting[player_seat] = amount
        logger.debug(
            "betting: player_seat = {}, amount = {}".format(player_seat, amount)
        )
        return True

    def showdown(self, player_seat: int):
        self.showdown_hands[player_seat] = self.hands[
            self.player_seating_chart[player_seat].id
        ]
        return

    def is_round_over(self):
        logger.debug("Table.is_round_over: checking is_round_over...")
        # そもそも参加者がいない場合
        if self.player_ongoing.count(True) == 0:
            logger.debug("Table.is_round_over: There is no player.")
            return False
        # 参加者が一人になった場合
        elif self.player_ongoing.count(True) == 1:
            logger.debug(
                "Table.is_round_over: There is only one ongoing player. Go to next round!"
            )
            return True

        # 参加者全員がプレイ済み　かつ　全員のベット額が一致
        return all(
            not self.player_ongoing[i] or self.played[i]
            for i in range(self.players_limit)
        ) and all(
            v == self.current_betting_amount
            for i, v in enumerate(self.betting)
            if self.player_ongoing[i]
        )

    def next_round_initialize(self):
        self.current_pot_size += reduce(lambda a, b: a + b, self.betting)
        self.betting = [0 for _ in self.betting]
        self.played = [False for _ in self.played]
        self.current_betting_amount = 0
        self.current_player = self.button_player
        self.next_player()

    def update_hand_rank(self):
        for player in self.player_seating_chart:
            if player is not None:
                self.hand_ranks[player.id] = HandRank(
                    self.hands[player.id] + self.board
                )
