from files.system.game_server import OnlinePlayer
from netlib import logs 
from files.media.assets import Assets
import asyncio

logs.init()

assets = Assets((32, 32))

client = OnlinePlayer(assets, id='Demecito')

asyncio.run(client.run())