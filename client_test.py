from files.logic.sets import Wildebeest, Chess, Shatranj
from files.system.server import GameServer, GameClient
from files.media.assets import Assets
from files.logic.serialization import deserialize
import asyncio


assets = Assets((76, 76))

client = GameClient(assets)

asyncio.run(client.run())