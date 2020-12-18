from functools import reduce
from abc import abstractmethod
import logging
import json
import random
from texasholdem.states import TableContext, ConcreteState
from texasholdem import Player, Table, SasakiJSONEncoder
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
            table.bet(
                table.current_player,
                msg["amount"],
            )
            table.current_betting_amount = msg["amount"]
            table.played[table.current_player] = True
            table.next_player()
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
                table.player_ongoing[seat_num] = True
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
        table.deck.shuffle()
        table.hands = [
            {"id": v.id, "hand": table.deck.draw(2)}
            for v in table.player_seating_chart
            if v is not None
        ]
        await table_context.set_table(table)
        await self.notify_player_hand(table_context)
        await table_context.set_state(PreflopStreetState())

    async def next_round(self, table_context: TableContext):
        pass


class PreflopStreetState(StreetState):
    async def notify_current_status(self, table_context: TableContext):
        table = table_context.get_table()
        resp = {
            "state": "preflop",
            "seating_chart": table.player_seating_chart,
            "button_player": table.button_player,
            "current_player": table.current_player,
            "betting": table.betting,
            "ongoing": table.player_ongoing,
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

    async def next_round(self, table_context: TableContext):
        table = table_context.get_table()
        table.next_round()
        table.board.extend(table.deck.draw(3).to_dict_list())
        await table_context.set_state(FlopStreetState())


class FlopStreetState(StreetState):
    async def notify_current_status(self, table_context: TableContext):
        table = table_context.get_table()
        resp = {
            "state": "flop",
            "seating_chart": table.player_seating_chart,
            "button_player": table.button_player,
            "current_player": table.current_player,
            "betting": table.betting,
            "ongoing": table.player_ongoing,
            "board": table.board,
            "pot_size": table.current_pot_size,
        }
        await broadcast(
            json.dumps(
                resp,
                cls=SasakiJSONEncoder,
            )
        )

    async def handle(self, table_context: TableContext, msg: dict):
        logger.debug("state: {}".format("Flop State"))
        await self.invoke_action(table_context, msg)

    async def next_round(self, table_context: TableContext):
        table = table_context.get_table()
        table.next_round()
        table.board.extend(table.deck.draw(1).to_dict_list())
        await table_context.set_state(TurnStreetState())


class TurnStreetState(StreetState):
    async def notify_current_status(self, table_context: TableContext):
        table = table_context.get_table()
        resp = {
            "state": "flop",
            "seating_chart": table.player_seating_chart,
            "button_player": table.button_player,
            "current_player": table.current_player,
            "betting": table.betting,
            "ongoing": table.player_ongoing,
            "board": table.board,
            "pot_size": table.current_pot_size,
        }
        await broadcast(
            json.dumps(
                resp,
                cls=SasakiJSONEncoder,
            )
        )

    async def handle(self, table_context: TableContext, msg: dict):
        logger.debug("state: {}".format("Turn State"))
        await self.invoke_action(table_context, msg)

    async def next_round(self, table_context: TableContext):
        table = table_context.get_table()
        table.next_round()
        table.board.extend(table.deck.draw(1).to_dict_list())
        await table_context.set_state(TurnStreetState())


class RiverStreetState(StreetState):
    async def handle(self, table_context: TableContext, msg: dict):
        logger.debug("state: {}".format("River State"))
        await self.invoke_action(table_context, msg)


class ShowdownState(GameState):
    async def handle(self, table_context: TableContext, msg: dict):
        logger.debug("state: {}".format("Showdown State"))
        await self.invoke_action(table_context, msg)
