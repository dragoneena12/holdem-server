import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

PLAYERS = {}


class Player:
    def __init__(self, player_id: str, name: str, bankroll: int):
        self.id = player_id
        self.name = name
        self.bankroll = bankroll

    def __eq__(self, other):
        if not isinstance(other, Player):
            return False
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)

    def __repr__(self):
        return str(self)

    def __str__(self):
        return self.id

    def toJSON(self):
        return {"id": self.id, "name": self.name, "bankroll": self.bankroll}

    def pay(self, amount: int):
        if self.bankroll >= amount:
            return True
        else:
            return False

    # 本当はnameはいらないけど生成しなきゃいけないので…。
    @staticmethod
    def get_player_by_id(player_id: str, player_name: str):
        if player_id in PLAYERS:
            return PLAYERS[player_id]
        else:
            return Player.generate_player(player_id, player_name)

    # 開発用メソッド。実際はDBに問い合わせたりする。
    @staticmethod
    def generate_player(player_id: str, player_name: str):
        PLAYERS[player_id] = Player(player_id, player_name, 1000)
        return PLAYERS[player_id]
