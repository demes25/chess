from files.boards import Wildebeest, Chess, Shatranj
from files.gui import *

pg.init()

standard_set = Wildebeest((76, 76))
bs = GUI(standard_set)
bs.run()

