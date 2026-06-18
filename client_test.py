from files.system.game_server import OnlinePlayer
from netlib import logs 
from files.media.assets import Assets
from files.media.schemes import CristiancitoScheme
from files.media.schemes import RaymacitaScheme
import asyncio

logs.init()

assets = Assets((64, 64), scheme=RaymacitaScheme)

client = OnlinePlayer(assets, id='Liamcito')

asyncio.run(client.run())