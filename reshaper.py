from netlib.filecaster import here 
from applib.utils import loader, saver, file_iter, new_surface
from pathlib import Path 

SRC = here('files', 'media', 'sprites', 'figures')
DEST = here('files', 'media', 'sprites', 'capt_figs')

load_func = loader()
save_func = saver(6/7)
plain_save = saver()

proj = new_surface((14, 14))

for name, sprite in file_iter(SRC, 'png', load_func):
    r = sprite.get_rect() 
    r.center = (7, 7)

    p = proj.copy()
    p.blit(sprite, r)

    save_func(p, Path(DEST, f'{name}.png'))

pproj = new_surface((13, 13))
for name, sprite in file_iter(DEST, 'png', load_func):
    p = pproj.copy()
    p.blit(sprite, (0, 0))
    plain_save(p, Path(DEST, f'{name}.png'))

    