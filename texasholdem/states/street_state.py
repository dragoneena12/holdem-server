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
        for p in table.player_seating_chart:
            if p is not None:
                unicast_msg[p.player.id] = {
                    "state": table.status,
                    "hand": p.hand,
                    "hand_rank": p.hand_rank,
                    "seating_chart": table.player_seating_chart,
                    "button_player": table.button_player,
                    "current_player": table.current_player,
                    "board": table.board,
                    "pot_size": table.current_pot_size,
                }
        broadcast_msg = {
            "state": table.status,
            "seating_chart": table.player_seating_chart,
            "button_player": table.button_player,
            "current_player": table.current_player,
            "board": table.board,
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
        if table.is_current_player(action_player):
            logger.debug("[ACTION] CALL")
            table.call()
            await table_context.set_table(table)

    async def action_raise(self, table_context: TableContext, msg: dict):
        table = table_context.get_table()
        action_player = self.get_action_player(msg)
        if table.is_current_player(action_player):
            logger.debug("[ACTION] RAISE: {}".format(msg["amount"]))
            table.action_raise(msg["amount"])
            await table_context.set_table(table)

    async def action_fold(self, table_context: TableContext, msg: dict):
        table = table_context.get_table()
        action_player = self.get_action_player(msg)
        if table.is_current_player(action_player):
            logger.debug("[ACTION] FOLD")
            table.fold()
            await table_context.set_table(table)


class BeforeGameState(GameState):
    async def action_seat(self, table_context: TableContext, msg: dict):
        table = table_context.get_table()
        seat_num = int(msg["amount"])
        action_player = self.get_action_player(msg)
        table.seat_player(action_player, seat_num)
        await table_context.set_table(table)

    async def action_leave(self, table_context: TableContext, msg: dict):
        table = table_context.get_table()
        action_player = self.get_action_player(msg)
        table.leave_player(action_player)
        await table_context.set_table(table)

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
            table.bet(table.stakes["SB"])
            table.next_player()
            table.bet(table.stakes["BB"])
            table.current_player = table.button_player
        else:
            table.next_player()
            table.bet(table.stakes["SB"])
            table.next_player()
            table.bet(table.stakes["BB"])
            table.next_player()
        table.status = "dealingHands"
        table.deck = Deck()
        table.deck.shuffle()
        for p in table.player_seating_chart():
            p.hand = table.deck.draw(2).cards
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
        await table_context.set_table(table)
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
        await table_context.set_table(table)
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
        await table_context.set_table(table)
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
        await table_context.set_table(table)
        await table_context.set_state(ShowdownState())


class ShowdownState(GameState):
    async def handle(self, table_context: TableContext, msg: dict):
        logger.debug("state: {}".format("Showdown State"))
        await self.invoke_action(table_context, msg)

    async def action_showdown(self, table_context: TableContext, msg: dict):
        table = table_context.get_table()
        action_player = self.get_action_player(msg)
        if table.is_current_player(action_player):
            logger.debug("[ACTION] SHOWDOWN")
            table.showdown()
            await table_context.set_table(table)

    async def action_muck(self, table_context: TableContext, msg: dict):
        table = table_context.get_table()
        action_player = self.get_action_player(msg)
        if table.is_current_player(action_player):
            logger.debug("[ACTION] MUCK")
            table.fold()
            await table_context.set_table(table)

    async def next_round(self, table_context: TableContext):
        table = table_context.get_table()
        table.next_round_initialize()
        if table.player_ongoing.count(True) > 1:
            pass
        table.status = "gameEnd"
        await table_context.set_table(table)
        await table_context.set_state(GameEndState())


class GameEndState(GameState):
    async def handle(self, table_context: TableContext, msg: dict):
        logger.debug("state: {}".format("GameEnd State"))
        await self.invoke_action(table_context, msg)

    async def action_check(self, table_context: TableContext, msg: dict):
        table = table_context.get_table()
        action_player = self.get_action_player(msg)
        if table.is_current_player(action_player):
            logger.debug("[ACTION] CHECK")
            table.check()
            await table_context.set_table(table)

    async def next_round(self, table_context: TableContext):
        table = table_context.get_table()
        table.game_end()
        table.status = "beforeGame"
        await table_context.set_table(table)
        await table_context.set_state(BeforeGameState())
