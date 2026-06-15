from files.logic.sets import Wildebeest, Chess, Shatranj
from files.system.game_server import OnlineGame
from netlib import logs
import asyncio

logs.init()

server = OnlineGame(Chess)

asyncio.run(server.run())


