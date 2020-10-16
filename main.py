#!/usr/bin/env python

# WS server example

import asyncio
import json
import logging

import websockets

from texasholdem import Deck, Table
from texasholdem.states import TableContext
from texasholdem.states.street_state import BeforeGameState
from websock import CLIENTS

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


async def hello(websocket, path):
    name = await websocket.recv()
    print(f"< {name}")

    greeting = f"Hello {name}!"

    await websocket.send(greeting)
    print(f"> {greeting}")


async def action_req_card(websocket, msg):
    deck = Deck()
    deck.shuffle()
    hand = deck.peek(2)

    send_msg = json.dumps({"hand": deck.peek(2).to_dict_list()})

    logger.debug("send message: {}".format(send_msg))
    await websocket.send(send_msg)


async def random_hand(websocket, path):
    async for message in websocket:
        logger.debug("websocket: {}".format(websocket))
        logger.debug("message: {}".format(message))
        msg = json.loads(message)
        action = msg["action"]
        if action == "reqCard":
            await action_req_card(websocket, msg)
        elif action in ["join"]:
            await websocket.send(json.dumps({"message": "action: {}".format()}))


async def websocket_queue_handler(
    websocket: websockets.server.WebSocketServerProtocol, path
):
    logger.debug("-" * 40)
    CLIENTS.append(websocket)
    try:
        async for message in websocket:
            logger.debug("websocket: {}".format(websocket))
            logger.debug("websocket local_address: {}".format(websocket.local_address))
            logger.debug(
                "websocket remote_address: {}".format(websocket.remote_address)
            )
            logger.debug("message: {}".format(message))

            msg = json.loads(message)
            await tableContext.handle(msg)
    except websockets.ConnectionClosedError:
        pass
    finally:
        CLIENTS.remove(websocket)


tableContext = TableContext(BeforeGameState(), Table(players_limit=6))

if __name__ == "__main__":
    start_server = websockets.serve(websocket_queue_handler, "0.0.0.0", 8765)

    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()
