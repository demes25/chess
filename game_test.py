from files.logic.logic import Engine, load_figures
from files.system.ui import to_UI

from applib.controls import fetch

from netlib.serialization import deserialize, serialize

import pygame as pg

ui = to_UI(4)

load_figures("files/logic/figures.json")

with open("files/logic/game.json") as f:
    game = f.read()


engine = Engine(game)
board = deserialize(engine.begin())

frontend = ui.GameInterface(board, 0)

pg.display.init()
screen = pg.display.set_mode(frontend.shape)

in_queue = []
out_queue = []

while True:
    out_queue = frontend.process(fetch())

    for outward in out_queue:
        in_queue.append(deserialize(engine.process(serialize(outward))))
    
    for inward in in_queue:
        frontend.register(inward)
    
    in_queue = []

    frontend.blit_onto(screen)
    



