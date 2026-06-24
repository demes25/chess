from files.logic.sets import Wildebeest, Chess, Shatranj
from files.ui.environment import GameWindow


GameWindow(Chess, (64, 64), default_time_s=400).run_solo()