from files.logic.sets import Wildebeest, Chess, Shatranj
from files.system.instance import GameInstance
from files.media.assets import Assets
from files.logic.serialization import deserialize

instance = GameInstance(Chess, Assets((76, 76)))
instance.run_solo()



