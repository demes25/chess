from files.media.assets import *

gui = GUI(Assets((76, 76)))

pg.display.init()
screen = pg.display.set_mode((gui.width, gui.height))

gui.board.blit_onto(screen)
pg.display.update()
input()