import asyncio
import logging
import json

from texasholdem import SasakiJSONEncoder
from websock import CLIENTS

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


async def broadcast(msg):
    await asyncio.gather(
        *[ws.send(msg) for ws in CLIENTS.values()], return_exceptions=False
    )


async def unicast(msg, client_id: int):
    await CLIENTS[client_id].send(msg)


async def notify(unicast_msg, broadcast_msg):
    logger.debug("notifying...")
    for player_id, m in unicast_msg.items():
        await unicast(
            json.dumps(
                m,
                cls=SasakiJSONEncoder,
            ),
            player_id,
        )
    for cliend_id in CLIENTS.keys():
        if cliend_id not in unicast_msg.keys():
            await unicast(json.dumps(broadcast_msg, cls=SasakiJSONEncoder), cliend_id)
