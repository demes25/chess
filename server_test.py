from files.logic.sets import Wildebeest, Chess, Shatranj
from files.system.server import GameServer
import asyncio

server = GameServer(Chess)

asyncio.run(server.run(host='0.0.0.0', enforce_player=True))


