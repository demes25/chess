from sets import *

game = Standard.Set()

from gui import *

pg.init()

bs = BoardScreen(game, (640, 640))
bs.run()

