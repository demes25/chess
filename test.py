from files.boards import Shatranj, Chess
from files.assets import IndianScheme
from files.gui import *

pg.init()

standard_set = Chess((80, 80))
bs = GUI(standard_set)
bs.run()

