from files.system.server import NetworkServer
from files.engine import load_figures, load_sets
from netlib import logs
import asyncio

load_sets('files/engine/sets.json')
load_figures('files/engine/figures.json')

logs.init()

server = NetworkServer()
asyncio.run(server.run())