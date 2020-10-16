import asyncio
import logging

from websock import CLIENTS

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


async def broadcast(msg):
    await asyncio.gather(*[ws.send(msg) for ws in CLIENTS], return_exceptions=False)

