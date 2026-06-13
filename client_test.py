from files.system.server import GameClient
from files.media.assets import Assets
import asyncio


assets = Assets((80, 80))

client = GameClient(assets)

asyncio.run(client.run())