from files.boards import Shatranj, Chess
from files.gui import *
from files.assets import LiamcitoScheme, IndianScheme, RaymacitaScheme

pg.init()

standard_set = Chess((96, 96), scheme=RaymacitaScheme)
bs = GUI(standard_set)
bs.run()

