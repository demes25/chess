from files.system.game_server import OnlinePlayer
from netlib import logs 
from files.media.assets import Assets
import asyncio

logs.init()

assets = Assets((80, 80))

client = OnlinePlayer(assets)

asyncio.run(client.run())