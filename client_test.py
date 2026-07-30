from files.system.client import NetworkClient, Address 
from files.media.assets import Assets
from files.media.schemes import CristiancitoScheme
from netlib import logs 
import asyncio, pygame as pg

import ctypes 

if hasattr(ctypes, 'windll'):
    myappid = 'demes25:obchessed:0.1.0' # arbitrary string
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    ctypes.windll.user32.SetProcessDPIAware()

logs.init()
pg.init()

assets = Assets(scaling=6, scheme=CristiancitoScheme)

client = NetworkClient(assets)
address = Address()

asyncio.run(client.run(address))