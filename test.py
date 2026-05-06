from files.sets import Shatranj, Chess
from files.graphics import Default
from files.gui import *

pg.init()

standard_set = Chess(Default, (80, 80))
bs = GUI(standard_set)
bs.run()

