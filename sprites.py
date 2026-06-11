import pygame as pg

old_path = 'files/media/sprites/figures/_16bit'
new_path = 'files/media/sprites/figures'

for piece in ['Alfil', 'Bishop', 'Camel', 'Ferz', 'King', 'Knight', 'Pawn', 'Queen', 'Rook', 'Wildebeest']:
    image = pg.image.load(f'{old_path}/{piece}.png')    
    image = pg.transform.scale(image, (32, 32))
    pg.image.save(image, f'{new_path}/{piece}.png')