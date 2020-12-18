import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


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

    @staticmethod
    def get_player_by_id(player_id: str):
        # TODO
        return Player(player_id, player_id, 1000)

    # 開発用メソッド。実際はDBに問い合わせたりする。
    @staticmethod
    def generate_player(player_id: str, player_name: str):
        # TODO
        return Player(player_id, player_name, 1000)
