from files.engine import Engine, load_figures
from files.engine.pyutils import Request
from files.system.ui import to_UI

from applib.controls import fetch

from netlib.serialization import deserialize, serialize

import pygame as pg

ui = to_UI(4)

load_figures("files/engine/figures.json")

with open("files/engine/game.json") as f:
    game = f.read()


engine = Engine(game)
board = deserialize(engine.begin())
board.enforce_player = False

frontend = ui.GameInterface(board, 0)

pg.init()
pg.display.init()
screen = pg.display.set_mode(frontend.shape)

in_queue = []
out_queue = []

print(str(engine))

while True:
    events = fetch()
    out_queue = frontend.process(events)

    for outward in out_queue:
        if isinstance(outward, Request) and outward.content == 'quit':
            quit()
        in_queue.append(engine.process(serialize(outward)))

        print("OUT " + serialize(outward))
    
    for inward in in_queue:
        print("IN " + inward)
        frontend.register(deserialize(inward))

    frontend.register(deserialize(engine.times()))
    
    in_queue = []

    frontend.blit_onto(screen)
    pg.display.flip()
    



