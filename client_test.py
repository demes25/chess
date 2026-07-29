from files.system.client import NetworkClient, Address 
from netlib import logs 
import asyncio, pygame as pg

import ctypes 

if hasattr(ctypes, 'windll'):
    ctypes.windll.user32.SetProcessDPIAware()

logs.init()
pg.init()

client = NetworkClient(6)
address = Address()

asyncio.run(client.run(address))