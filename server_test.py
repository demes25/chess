from files.logic.sets import Wildebeest, Chess, Shatranj
from files.system.game_server import OnlineGame
from netlib.server import Address
from netlib import logs
import asyncio

logs.init()

server = OnlineGame(Chess, default_time_s=1200)

asyncio.run(server.run(Address('0.0.0.0', 8888)))


