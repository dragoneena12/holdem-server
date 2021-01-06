import logging
import random
from texasholdem.states import TableContext, ConcreteState
from texasholdem import Player, Table, Deck
from websock import notify

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class GameState(ConcreteState):
    async def handle(self, table_context: TableContext, msg: dict):
        await self.invoke_action(table_context, msg)

    async def invoke_action(self, table_context: TableContext, msg: dict):
        action_name = msg["action"]
        try:
            await getattr(self, f"action_{action_name}")(table_context, msg)
        except AttributeError:
            # 目的のアクションがない場合
            pass

    def get_action_player(self, msg: dict):
        player_id = msg["client_id"]
        player_name = msg["name"]
        return Player.get_player_by_id(player_id, player_name)

    async def notify_current_status(self, table_context: TableContext):
        logger.debug("lets notify!")
        table = table_context.get_table()
        unicast_msg = {}
        for player_id, hand in table.hands.items():
            unicast_msg[player_id] = {
                "state": table.status,
                "hand": [c.to_dict() for c in hand],
                "hand_rank": str(table.hand_ranks[player_id])
                if player_id in table.hand_ranks
                else None,
                "showdown_hands": [
                    [c.to_dict() for c in h] if h is not None else None
                    for h in table.showdown_hands
                ],
                "seating_chart": table.player_seating_chart,
                "button_player": table.button_player,
                "current_player": table.current_player,
                "betting": table.betting,
                "ongoing": table.player_ongoing,
                "board": [c.to_dict() for c in table.board],
                "pot_size": table.current_pot_size,
            }
        broadcast_msg = {
            "state": table.status,
            "hand": [],
            "showdown_hands": [
                [c.to_dict() for c in h] if h is not None else None
                for h in table.showdown_hands
            ],
            "seating_chart": table.player_seating_chart,
            "button_player": table.button_player,
            "current_player": table.current_player,
            "betting": table.betting,
            "ongoing": table.player_ongoing,
            "board": [c.to_dict() for c in table.board],
            "pot_size": table.current_pot_size,
        }
        await notify(unicast_msg, broadcast_msg)

    async def action_reset(self, table_context: TableContext, msg: dict):
        await table_context.set_table(Table(players_limit=6))
        await table_context.set_state(BeforeGameState())


class StreetState(GameState):
    async def action_check(self, table_context: TableContext, msg: dict):
        await self.action_call(table_context, msg)

    async def action_bet(self, table_context: TableContext, msg: dict):
        await self.action_raise(table_context, msg)

    async def action_call(self, table_context: TableContext, msg: dict):
        table = table_context.get_table()
        action_player = self.get_action_player(msg)
        if action_player is table.player_seating_chart[table.current_player]:
            logger.debug("[ACTION] CALL")
            table.bet(
                table.current_player,
                table.current_betting_amount,
            )
            table.played[table.current_player] = True
            table.next_player()
            await table_context.set_table(table)
        else:
            return

    async def action_raise(self, table_context: TableContext, msg: dict):
        table = table_context.get_table()
        action_player = self.get_action_player(msg)
        if action_player is table.player_seating_chart[table.current_player]:
            logger.debug("[ACTION] RAISE: {}".format(msg["amount"]))
            if msg["amount"] <= table.current_betting_amount:
                return
            if table.bet(
                table.current_player,
                msg["amount"],
            ):
                table.current_betting_amount = msg["amount"]
                table.played[table.current_player] = True
                table.next_player()
            else:
                return
            await table_context.set_table(table)
        else:
            return

    async def action_fold(self, table_context: TableContext, msg: dict):
        table = table_context.get_table()
        action_player = self.get_action_player(msg)
        if action_player is table.player_seating_chart[table.current_player]:
            logger.debug("[ACTION] FOLD")
            table.player_ongoing[table.current_player] = False
            table.next_player()
            await table_context.set_table(table)
        else:
            return


class BeforeGameState(GameState):
    async def action_seat(self, table_context: TableContext, msg: dict):
        table = table_context.get_table()
        seat_num = int(msg["amount"])
        action_player = self.get_action_player(msg)
        try:
            if (
                table.player_seating_chart[seat_num] is None
                and action_player not in table.player_seating_chart
            ):
                table.player_seating_chart[seat_num] = action_player
                table.player_num += 1
                table.player_ongoing[seat_num] = True
                table.hands[action_player.id] = []
                await table_context.set_table(table)
            else:
                pass
        except IndexError:
            pass

    async def action_leave(self, table_context: TableContext, msg: dict):
        table = table_context.get_table()
        seat_num = int(msg["amount"])
        action_player = self.get_action_player(msg)
        try:
            if table.player_seating_chart[seat_num] == action_player:
                table.player_seating_chart[seat_num] = None
                table.player_num -= 1
                table.player_ongoing[seat_num] = False
                table.hands.pop(action_player.id)
                await table_context.set_table(table)
            else:
                pass
        except IndexError:
            pass

    async def action_start(self, table_context: TableContext, msg: dict):
        table = table_context.get_table()
        if table.player_num < 2:
            return
        logger.debug("state: {}".format("Game Start!"))
        table = table_context.get_table()
        if table.current_player == -1:
            table.current_player = random.randint(0, table.players_limit - 1)
        else:
            table.current_player = table.button_player
        table.next_player()
        table.button_player = table.current_player
        if table.player_num == 2:
            table.bet(table.current_player, table.stakes["SB"])
            table.next_player()
            table.bet(
                table.current_player,
                table.stakes["BB"],
            )
            table.current_betting_amount = table.stakes["BB"]
            table.current_player = table.button_player
        else:
            table.next_player()
            table.bet(table.current_player, table.stakes["SB"])
            table.next_player()
            table.bet(table.current_player, table.stakes["BB"])
            table.current_betting_amount = table.stakes["BB"]
            table.next_player()
        table.status = "dealingHands"
        table.deck = Deck()
        table.deck.shuffle()
        for player_id in table.hands.keys():
            table.hands[player_id] = table.deck.draw(2).cards
        await table_context.set_table(table)
        table.status = "preflop"
        await table_context.set_table(table)
        await table_context.set_state(PreflopStreetState())

    async def next_round(self, table_context: TableContext):
        pass


class PreflopStreetState(StreetState):
    async def handle(self, table_context: TableContext, msg: dict):
        logger.debug("state: {}".format("Pre-flop State"))
        await self.invoke_action(table_context, msg)

    async def next_round(self, table_context: TableContext):
        table = table_context.get_table()
        table.next_round_initialize()
        if table.player_ongoing.count(True) > 1:
            table.board.extend(table.deck.draw(3).cards)
            table.update_hand_rank()
        table.status = "flop"
        await table_context.set_state(FlopStreetState())


class FlopStreetState(StreetState):
    async def handle(self, table_context: TableContext, msg: dict):
        logger.debug("state: {}".format("Flop State"))
        await self.invoke_action(table_context, msg)

    async def next_round(self, table_context: TableContext):
        table = table_context.get_table()
        table.next_round_initialize()
        if table.player_ongoing.count(True) > 1:
            table.board.extend(table.deck.draw(1).cards)
            table.update_hand_rank()
        table.status = "turn"
        await table_context.set_state(TurnStreetState())


class TurnStreetState(StreetState):
    async def handle(self, table_context: TableContext, msg: dict):
        logger.debug("state: {}".format("Turn State"))
        await self.invoke_action(table_context, msg)

    async def next_round(self, table_context: TableContext):
        table = table_context.get_table()
        table.next_round_initialize()
        if table.player_ongoing.count(True) > 1:
            table.board.extend(table.deck.draw(1).cards)
            table.update_hand_rank()
        table.status = "river"
        await table_context.set_state(RiverStreetState())


class RiverStreetState(StreetState):
    async def handle(self, table_context: TableContext, msg: dict):
        logger.debug("state: {}".format("River State"))
        await self.invoke_action(table_context, msg)

    async def next_round(self, table_context: TableContext):
        table = table_context.get_table()
        table.next_round_initialize()
        if table.player_ongoing.count(True) > 1:
            pass
        table.status = "showdown"
        await table_context.set_state(ShowdownState())


class ShowdownState(GameState):
    async def handle(self, table_context: TableContext, msg: dict):
        logger.debug("state: {}".format("Showdown State"))
        await self.invoke_action(table_context, msg)

    async def action_showdown(self, table_context: TableContext, msg: dict):
        table = table_context.get_table()
        action_player = self.get_action_player(msg)
        if action_player is table.player_seating_chart[table.current_player]:
            logger.debug("[ACTION] SHOWDOWN")
            table.showdown(
                table.current_player,
            )
            table.played[table.current_player] = True
            table.next_player()
            await table_context.set_table(table)
        else:
            return

    async def action_muck(self, table_context: TableContext, msg: dict):
        table = table_context.get_table()
        action_player = self.get_action_player(msg)
        if action_player is table.player_seating_chart[table.current_player]:
            logger.debug("[ACTION] MUCK")
            table.player_ongoing[table.current_player] = False
            table.next_player()
            await table_context.set_table(table)
        else:
            return

    async def next_round(self, table_context: TableContext):
        table = table_context.get_table()
        table.next_round_initialize()
        if table.player_ongoing.count(True) > 1:
            pass
        table.status = "gameEnd"
        await table_context.set_state(GameEndState())


class GameEndState(GameState):
    async def handle(self, table_context: TableContext, msg: dict):
        logger.debug("state: {}".format("GameEnd State"))
        await self.invoke_action(table_context, msg)

    async def action_check(self, table_context: TableContext, msg: dict):
        table = table_context.get_table()
        action_player = self.get_action_player(msg)
        if action_player is table.player_seating_chart[table.current_player]:
            logger.debug("[ACTION] CHECK")
            table.played[table.current_player] = True
            table.next_player()
            await table_context.set_table(table)
        else:
            return

    async def next_round(self, table_context: TableContext):
        table = table_context.get_table()
        if table.player_ongoing.count(True) == 1:
            table.player_seating_chart[
                table.player_ongoing.index(True)
            ].bankroll += table.current_pot_size
        else:
            winner_index = None
            winner_rank = None
            for i in range(table.players_limit):
                if table.player_ongoing[i]:
                    if winner_index is None:
                        winner_index = i
                        winner_rank = table.hand_ranks[i]
                    else:
                        if table.hand_ranks[i] > winner_rank:
                            winner_index = i
                            winner_rank = table.hand_ranks[i]
            table.player_seating_chart[winner_index].bankroll += table.current_pot_size

        # 初期化処理
        table.hands = {}
        for player in table.player_seating_chart:
            if player is not None:
                table.hands[player.id] = []
        table.hand_ranks = {}
        table.board = []
        table.betting = [0 for _ in range(table.players_limit)]
        table.player_ongoing = [v is not None for v in table.player_seating_chart]
        table.played = [False for _ in range(table.players_limit)]
        table.showdown_hands = [None for _ in range(table.players_limit)]
        table.current_betting_amount = 0
        table.current_pot_size = 0
        table.status = "beforeGame"
        await table_context.set_state(BeforeGameState())
