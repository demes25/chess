from files.engine import Engine, load_figures, load_sets, Request 

from files.system.graph import Processor
from files.system.ui import to_UI

from applib.controls import fetch

from netlib.serialization import deserialize, serialize

import pygame as pg

ui = to_UI(4)

load_figures("files/engine/figures.json")
load_sets("files/engine/sets.json")


processor = Processor("Chess", 600)
layout = processor.begin()

print(layout.content)
board = deserialize(layout.content)

frontend = ui.GameInterface(board, 0, False)

pg.init()
pg.display.init()
screen = pg.display.set_mode(frontend.shape)

in_queue = []
out_queue = []

print(str(processor.instance.engine))

while True:
    events = fetch()
    out_queue = frontend.process(events)

    for outward in out_queue:
        if isinstance(outward, Request) and outward.label == 'quit':
            quit()
        in_queue.append(processor.process(outward))

        print("OUT " + serialize(outward))
    
    for inward in in_queue:
        print("IN " + serialize(inward))
        frontend.register(inward)

    frontend.register(processor.instance.engine.times())
    
    in_queue = []

    frontend.blit_onto(screen)
    pg.display.flip()
    



