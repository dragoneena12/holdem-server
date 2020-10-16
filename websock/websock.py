import asyncio
import logging

from websock import CLIENTS

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def broadcast(msg):
    for ws in CLIENTS:
        ws.send(msg)

