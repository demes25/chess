from files.logic.sets import Wildebeest, Chess, Shatranj
from files.system.server import GameServer, GameClient, GameInstance
from files.media.assets import Assets
from files.logic.serialization import deserialize
import asyncio

#instance = GameInstance(Chess, Assets((76, 76)))
#instance.run_solo()


server = GameServer(Chess)

asyncio.run(server.run(enforce_player=True))


