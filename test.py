from files.sets import Shatranj
from files.graphics import Default
from files.gui import *

pg.init()

standard_set = Shatranj(Default, (80, 80))
bs = GUI(standard_set)
bs.run()

