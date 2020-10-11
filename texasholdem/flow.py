# Poker
from texasholdem import Player, NotEnoughPlayerError, PlayerLimitExceededError, NotEnoughPlayerBankrollError, \
    OutOfBuyInRangeError, OccupiedSeatError, Deck
from texasholdem.table import Table

import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

table = Table(name="mytable")

logger.debug(
    "Creater new table. (id={})".format(
        table.id
    )
)

table.max_player = 2
table.stakes
{
    "BB": 2,
    "SB": 1,
    "ante": 0,
}

logger.debug(
    "Table Information. {}".format(
        table
    )
)

player_sasaki = Player(
    name="Sasaki",
    bankroll=10000
)

player_lapi = Player(
    name="Lapi",
    bankroll=10000
)

try:
    table.add_players([player_sasaki, player_lapi])
except PlayerLimitExceededError as e:
    # 人数制限を超えた場合
    raise e

try:
    table.seat_player(
        player=player_sasaki,
        seat_number=seat_number,
    )
except OccupiedSeatError as e:
    # 席が空いていない場合
    raise e
finally:
    pass
# 最終処理


try:
    table.buy_in(
        player=player_sasaki,
        amount=200,
    )
except NotEnoughPlayerBankrollError as e:
    # Bankroll不足
    raise e
except OutOfBuyInRangeError as e:
    # Buy-in範囲
    raise e
finally:
    # 最終処理
    pass
# ゲームの開始準備
# BB決めたり


try:
    table.initialize()
except NotEnoughPlayerError as e:
    # 人数不足の場合
    raise e
while table.isActive():
    # ハンドを進める
    play_hand(hand)
    # Playerの増減処理
    # バイイン
    # 次のハンドへ(BBの移動など)
    table.next_hand()


# ゲーム終了処理


def play_hand(table):
    # Initialise
    cards = Deck()
    cards.shuffle()  # 乱数シードを記録

    order_of_players = [p for p in table.order_of_players if isinstance(p, Player)]

    # プレイヤーに十分なスタックがあるか確認
    # Pre-Flop
    # Flop
    # Turn
    # River
