from files.logic.sets import Wildebeest, Chess, Shatranj
from files.app import *

pg.init()

bs = App(Chess, assets=Assets((76, 76)))
bs.run()

