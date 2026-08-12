from files.engine import load_figures, load_sets, EngineRequest 

from files.system.items import Session, Request, UserLayout, Error, Challenge, Response
from files.system.ui import to_UI

from applib.controls import fetch

from netlib.serialization import deserialize, serialize

import pygame as pg

ui = to_UI(4)

load_figures("files/engine/figures.json")
load_sets("files/engine/sets.json")


processor = Session("Wildebeest", 300, ("", ""))
layout = processor.begin()

print(layout.board_str)
board = deserialize(layout.board_str)

pg.init()
pg.display.init()

#TODO: errors have arisen. the king was able to be next to the enemy king. This is a bug in the engine, not the UI. The engine should be fixed to prevent this from happening.

frontend = ui.GameInterface(board, 0, False)
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
'''


#frontend = ui.AuthInterface(25)

frontend = ui.MiddleInterface('deme', 36, 6.5)
frontend.add(
    UserLayout('joaco')
)
frontend.add(
    UserLayout('cristiancito')
)

screen = pg.display.set_mode(frontend.shape)

frontend.show_message(Error(label="error", content="test error"), 5)
#frontend.show_challenge(Challenge('joaco', 'deme', 'Chess', 600))

#frontend.show_challenge(Challenge('cristiancito', 'deme', 'Chess', 600))

while True:
    events = fetch()
    out_queue = frontend.process(events)

    for outward in out_queue:
        print(outward)

    frontend.blit_onto(screen)
    pg.display.flip()
'''