from files.boards import Wildebeest, Chess
from files.gui import *
from files.assets import LiamcitoScheme, IndianScheme, RaymacitaScheme

pg.init()

standard_set = Wildebeest((76, 76))
bs = GUI(standard_set)
bs.run()

