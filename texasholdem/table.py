from texasholdem import Player
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
        self.player_seating_chart = [None for _ in range(players_limit)]
        self.player_status = {}  # type: Dict[Player, Dict]
        self.status = {
            "player_order": [],  # type: List[Player]
        }
        self.current_player = 0  # 0 = SB

    def __eq__(self, other):
        if not isinstance(other, Table):
            return False
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)

    def __change_stakes(self, sb: int, bb: int, ante=0):
        self.stakes = {"SB": sb, "BB": bb, "ante": ante}

