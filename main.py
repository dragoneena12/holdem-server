#!/usr/bin/env python

# WS server example

import asyncio
import json

import websockets
import logging

from texasholdem import Deck

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


async def hello(websocket, path):
    name = await websocket.recv()
    print(f"< {name}")

    greeting = f"Hello {name}!"

    await websocket.send(greeting)
    print(f"> {greeting}")


async def random_hand(websocket, path):
    async for message in websocket:
        logger.debug("websocket: {}".format(websocket))
        logger.debug("message: {}".format(message))
        msg = json.loads(message)

        ret = msg.message

        await websocket.send(ret)


if __name__ == '__main__':
    start_server = websockets.serve(random_hand, "0.0.0.0", 8765)

    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()
