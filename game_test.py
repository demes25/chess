from files.logic.sets import Wildebeest, Chess, Shatranj
from files.ui.windows import GameWindow


GameWindow(Chess, 4, default_time_s=400).run_solo()