from files.logic.sets import Wildebeest, Chess, Shatranj
from files.system.environment import GameWindow, Assets


GameWindow(Chess, assets=Assets((76, 76))).run_solo()