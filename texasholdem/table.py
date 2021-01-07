from functools import reduce

from texasholdem import Player, Deck, Card, HandRank
from typing import List

import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class GamingPlayer:
    def __init__(self, player: Player):
        self.player = player
        self.hand = []  # type: List[Card]
        self.hand_rank: HandRank = None
        self.betting = 0
        self.ongoing = True
        self.played = False
        self.is_showdown = False

    def toJSON(self):
        return {
            "player": self.player,
            "hand": self.hand if self.is_showdown else [Card(0, "B"), Card(0, "B")],
            "betting": self.betting,
            "ongoing": self.ongoing,
        }


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
        ]  # type: List[GamingPlayer]
        self.board = []
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

    def __find_player_index(self, player: Player):
        logger.debug("__find_player_index called")
        for i in range(self.players_limit):
            if self.player_seating_chart[i] is not None:
                if self.player_seating_chart[i].player is player:
                    return i
        return None

    def seat_player(self, player: Player, seat_num: int):
        logger.debug("seat_player called")
        logger.debug(
            "seat_player: can player seat? {}, {}".format(
                self.player_seating_chart[seat_num] is None,
                self.__find_player_index(player) is None,
            )
        )
        if (
            self.player_seating_chart[seat_num] is None
            and self.__find_player_index(player) is None
        ):
            self.player_seating_chart[seat_num] = GamingPlayer(player)
            self.player_num += 1

    def leave_player(self, player: Player):
        seat_num = self.__find_player_index(player)
        if seat_num is not None:
            self.player_seating_chart[seat_num] = None
            self.player_num -= 1

    def next_player(self):
        logger.debug("next_player: current_player = {}".format(self.current_player))
        cp = self.current_player
        cp = (cp + 1) % self.players_limit
        while (
            not self.player_seating_chart[cp].ongoing
            if self.player_seating_chart[cp] is not None
            else True
        ):
            logger.debug("cp: {}".format(cp))
            cp = (cp + 1) % self.players_limit
        logger.debug("next player is {} !".format(cp))
        self.current_player = cp

    def bet(self, amount: int):
        if not self.player_seating_chart[self.current_player].player.pay(
            amount - self.player_seating_chart[self.current_player].betting
        ):
            logger.debug("state: {}".format("Bankroll in not enough."))
            # raise Exception("Bankroll in not enough.") TODO: いい感じの例外クラスを作る
            return False
        self.player_seating_chart[self.current_player].betting = amount
        self.current_betting_amount = amount
        logger.debug(
            "betting: current_player = {}, amount = {}".format(
                self.current_player, amount
            )
        )
        return True

    def call(self):
        if self.bet(self.current_betting_amount):
            self.player_seating_chart[self.current_player].played = True
            self.next_player()

    def action_raise(self, amount: int):
        if amount < self.current_betting_amount:
            return
        if self.bet(amount):
            self.player_seating_chart[self.current_player].played = True
            self.next_player()

    def fold(self):
        self.player_seating_chart[self.current_player].ongoing = False
        self.next_player()

    def check(self):
        if self.current_betting_amount == 0:
            self.player_seating_chart[self.current_player].played = True
            self.next_player()

    def showdown(self):
        self.player_seating_chart[self.current_player].is_showdown = True
        self.player_seating_chart[self.current_player].played = True
        self.next_player()

    def ongoing_players_count(self):
        n = 0
        for p in self.player_seating_chart:
            if p is not None:
                if p.ongoing:
                    n += 1
        return n

    def is_current_player(self, player: Player):
        logger.debug("is_current_player called")
        return (
            self.player_seating_chart[self.current_player]
            and self.player_seating_chart[self.current_player].player.id == player.id
        )

    def is_round_over(self):
        logger.debug("Table.is_round_over: checking is_round_over...")

        ongoing_players_count = self.ongoing_players_count()

        # そもそも参加者がいない場合
        if ongoing_players_count == 0:
            logger.debug("Table.is_round_over: There is no player.")
            return False
        # 参加者が一人になった場合
        elif ongoing_players_count == 1:
            logger.debug(
                "Table.is_round_over: There is only one ongoing player. Go to next round!"
            )
            return True

        is_all_played = all(
            not self.player_seating_chart[i].ongoing
            or self.player_seating_chart[i].played
            for i in range(self.players_limit)
            if self.player_seating_chart[i] is not None
        )

        is_match_all_betting_amount = all(
            self.player_seating_chart[i].betting == self.current_betting_amount
            for i in range(self.players_limit)
            if self.player_seating_chart[i] is not None
            and self.player_seating_chart[i].ongoing
        )

        logger.debug(
            "is_all_played: {}, is_match_all_betting_amount: {}".format(
                is_all_played, is_match_all_betting_amount
            )
        )

        # 参加者全員がプレイ済み　かつ　全員のベット額が一致
        return is_all_played and is_match_all_betting_amount

    def next_round_initialize(self):
        logger.debug("next_round_initialize called")
        for p in self.player_seating_chart:
            if p is not None:
                self.current_pot_size += p.betting
                p.betting = 0
                p.played = False
        self.current_betting_amount = 0
        self.current_player = self.button_player
        self.next_player()

    def update_hand_rank(self):
        logger.debug("update_hand_rank called")
        for p in self.player_seating_chart:
            if p is not None:
                p.hand_rank = HandRank(p.hand + self.board)

    def game_end(self):
        logger.debug("game_end called")
        ongoing_players_count = 0
        ongoing_player = None
        for p in self.player_seating_chart:
            if p is not None and p.ongoing:
                ongoing_players_count += 1
                ongoing_player = p

        if ongoing_players_count == 1:
            logger.debug("only one player is ongoing")
            ongoing_player.bankroll += self.current_pot_size
        else:
            logger.debug("there are multiple players ongoing")
            winner_index = None
            winner_rank = None
            for i in range(self.players_limit):
                logger.debug("i: {}".format(i))
                if self.player_seating_chart[i] is not None:
                    if self.player_seating_chart[i].ongoing:
                        if winner_index is None:
                            winner_index = i
                            winner_rank = self.player_seating_chart[i].hand_rank
                        else:
                            if self.player_seating_chart[i].hand_rank > winner_rank:
                                winner_index = i
                                winner_rank = self.player_seating_chart[i].hand_rank
            logger.debug("winner is {}".format(i))
            self.player_seating_chart[
                winner_index
            ].player.bankroll += self.current_pot_size

        logger.debug("initializing...")
        # 初期化処理
        self.board = []
        self.current_betting_amount = 0
        self.current_pot_size = 0
        for p in self.player_seating_chart:
            if p is not None:
                p.hand = []
                p.hand_rank = None
                p.played = False
                p.ongoing = True
                p.is_showdown = False
