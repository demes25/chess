from files.logic.sets import Wildebeest, Chess, Shatranj
from files.system.instance import GameInstance
from files.media.assets import Assets

GameInstance(Wildebeest, Assets((76, 76))).run_solo()

