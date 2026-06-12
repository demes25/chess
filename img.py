from files.media.schemes import CristiancitoScheme
from files.media.assets import Assets, new_surface, Path
import pygame as pg 

H = W = 384

backend = Assets((W, H), CristiancitoScheme, sprite_size=1.0)

tiles = backend.colored_tiles
surface = new_surface((W*8, H*8))

for i in range(8):
    for j in range(8):
        # Alternate color based on position
        tile = tiles[(i+j) % 2]

        surface.blit(tile, (j * W, i * H))

pg.image.save(surface, 'board.png')

pg.image.save(backend.colored_figures[1]['King'], 'black_king.png')
pg.image.save(backend.colored_figures[0]['King'], 'white_king.png')
pg.image.save(backend.colored_figures[0]['Queen'], 'white_queen.png')

font = pg.font.Font(Path(backend.asset_dir, f'title_font.{backend.font_ext}'), 48)        
text = font.render('OBCHESSED', True, CristiancitoScheme['tile_white'])
s_text = font.render('OBCHESSED', True, CristiancitoScheme['player_white'])

text = pg.transform.scale(text, (800, 123))
s_text = pg.transform.scale(s_text, (800, 123))

pg.image.save(text, 'text.png')
pg.image.save(s_text, 's_text.png')