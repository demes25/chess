from files.media.assets import Assets
from pygame.image import save

a = Assets()
save(a.make_raw_plaque((67, 15), small_corners=True), 'plaque.png')