from files.logic.sets import Wildebeest, Chess, Shatranj
from files.app import *

pg.init()

bs = App(Wildebeest, assets=Assets((76, 76)))
bs.run()

