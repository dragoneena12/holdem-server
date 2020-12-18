from websockets import client


CLIENTS = {}
client_id_count = 0
from websock.websock import broadcast, unicast, notify
