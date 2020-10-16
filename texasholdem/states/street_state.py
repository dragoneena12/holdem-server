from abc import abstractmethod
import logging
import json
from texasholdem.states import TableContext, ConcreteState
from texasholdem import Player, SasakiJSONEncoder
from websock import broadcast

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
        player_id = msg["name"]
        return Player.get_player_by_id(player_id)


class StreetState(GameState):
    def action_check(self, table_context: TableContext, msg: dict):
        raise NotImplementedError()

    def action_bet(self, table_context: TableContext, msg: dict):
        raise NotImplementedError()

    def action_call(self, table_context: TableContext, msg: dict):
        raise NotImplementedError()

    def action_raise(self, table_context: TableContext, msg: dict):
        raise NotImplementedError()

    def action_fold(self, table_context: TableContext, msg: dict):
        raise NotImplementedError()


class BeforeGameState(GameState):
    async def notify_current_status(self, table_context: TableContext):
        resp = {
            "state": "beforeGame",
            "seating_chart": table_context.get_table().player_seating_chart,
        }
        await broadcast(json.dumps(resp, cls=SasakiJSONEncoder,))

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
            if table.player_seating_chart[seat_num] is action_player:
                table.player_seating_chart[seat_num] = None
                await table_context.set_table(table)
            else:
                pass
        except IndexError:
            pass

    async def action_start(self, table_context: TableContext, msg: dict):
        logger.debug("state: {}".format("Game Start!"))
        await table_context.set_state(PreflopStreetState())


class PreflopStreetState(StreetState):
    def __init__(self):
        # 順番をUTGからにする
        pass

    async def handle(self, table_context: TableContext, msg: dict):
        logger.debug("state: {}".format("Pre-flop State"))
        await self.invoke_action(table_context, msg)


class FlopStreetState(StreetState):
    def handle(self, table_context: TableContext):
        logger.debug("state: {}".format("Flop State"))
        table_context.set_state(TurnStreetState())


class TurnStreetState(StreetState):
    def handle(self, table_context: TableContext):
        logger.debug("state: {}".format("Turn State"))
        table_context.set_state(RiverStreetState())


class RiverStreetState(StreetState):
    def handle(self, table_context: TableContext):
        logger.debug("state: {}".format("River State"))


class ShowdownState(GameState):
    def handle(self, table_context: TableContext):
        logger.debug("state: {}".format("Showdown State"))
        table_context.set_state(PreflopStreetState())
