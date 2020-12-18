from abc import abstractmethod
import logging
import json
import random
from texasholdem.states import TableContext, ConcreteState
from texasholdem import Player, SasakiJSONEncoder
from websock import broadcast, unicast

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

    def next_player(self, table):
        cp = table.current_player
        cp = (cp + 1) % table.players_limit
        while table.player_seating_chart[cp] is None:
            cp = (cp + 1) % table.players_limit
        logger.debug("next player is {} !".format(cp))
        table.current_player = cp

    def betting(self, player_seat: int, amount: int, table):
        if not table.player_seating_chart[player_seat].pay(
            amount - table.betting[player_seat]
        ):
            logger.debug("state: {}".format("Bankroll in not enough."))
            raise Exception("Bankroll in not enough.")  # TODO: いい感じの例外クラスを作る
        table.betting[player_seat] = amount
        logger.debug(
            "betting: player_seat = {}, amount = {}".format(player_seat, amount)
        )


class StreetState(GameState):
    async def action_check(self, table_context: TableContext, msg: dict):
        raise NotImplementedError()

    async def action_bet(self, table_context: TableContext, msg: dict):
        raise NotImplementedError()

    async def action_call(self, table_context: TableContext, msg: dict):
        table = table_context.get_table()
        action_player = self.get_action_player(msg)
        if action_player is table.player_seating_chart[table.current_player]:
            logger.debug("[ACTION] CALL")
            self.betting(
                table.current_player,
                table.current_betting_amount,
                table,
            )
            self.next_player(table)
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
            self.betting(
                table.current_player,
                msg["amount"],
                table,
            )
            table.current_betting_amount = msg["amount"]
            self.next_player(table)
            await table_context.set_table(table)
        else:
            return

    async def action_fold(self, table_context: TableContext, msg: dict):
        raise NotImplementedError()


class BeforeGameState(GameState):
    async def notify_current_status(self, table_context: TableContext):
        resp = {
            "state": "beforeGame",
            "seating_chart": table_context.get_table().player_seating_chart,
        }
        await broadcast(
            json.dumps(
                resp,
                cls=SasakiJSONEncoder,
            )
        )

    async def notify_player_hand(self, table_context: TableContext):
        table = table_context.get_table()
        for h in table.hands:
            msg = {"state": "dealingHands", "hand": h["hand"].to_dict_list()}
            await unicast(
                json.dumps(
                    msg,
                    cls=SasakiJSONEncoder,
                ),
                h["id"],
            )

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
        table.current_player = random.randint(0, table.players_limit - 1)
        self.next_player(table)
        table.button_player = table.current_player
        if table.player_num == 2:
            self.betting(table.current_player, table.stakes["SB"], table)
            self.next_player(table)
            self.betting(
                table.current_player,
                table.stakes["BB"],
                table,
            )
            table.current_betting_amount = table.stakes["BB"]
            table.current_player = table.button_player
        else:
            self.next_player(table)
            self.betting(table.current_player, table.stakes["SB"], table)
            self.next_player(table)
            self.betting(table.current_player, table.stakes["BB"], table)
            table.current_betting_amount = table.stakes["BB"]
            self.next_player(table)
        table.deck.shuffle()
        table.hands = [
            {"id": v.id, "hand": table.deck.draw(2)}
            for v in table.player_seating_chart
            if v is not None
        ]
        await table_context.set_table(table)
        await self.notify_player_hand(table_context)
        await table_context.set_state(PreflopStreetState())


class PreflopStreetState(StreetState):
    async def notify_current_status(self, table_context: TableContext):
        table = table_context.get_table()
        resp = {
            "state": "preflop",
            "seating_chart": table.player_seating_chart,
            "button_player": table.button_player,
            "current_player": table.current_player,
            "betting": table.betting,
        }
        await broadcast(
            json.dumps(
                resp,
                cls=SasakiJSONEncoder,
            )
        )

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
