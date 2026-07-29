from files.system.server import NetworkServer
from files.engine import load_figures, load_sets
from netlib import logs
from netlib.server import Address
import asyncio

load_sets('files/engine/sets.json')
load_figures('files/engine/figures.json')

logs.init()

server = NetworkServer()
address = Address('0.0.0.0')

asyncio.run(server.run(address))