from files.system.client import NetworkClient
from netlib import logs 
import asyncio, pygame as pg

logs.init()
pg.init()

client = NetworkClient(4)

asyncio.run(client.run())