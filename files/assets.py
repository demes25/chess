# Demetre Seturidze
# Chess
# Assets

from typing import Tuple, Dict
import pygame as pg

Color = Tuple[int, int, int]
Scheme = Dict[str, Color]

Sound = pg.mixer.Sound
SFX = Dict[str, Sound]

Surface = pg.surface.Surface 

pg.init()
pg.mixer.init()


def new_surface(dims : Tuple[int, int]):
    return Surface(dims, pg.SRCALPHA)

# tints an image in-place (and returns)
def tint(surface : Surface, color : Color, opacity : int = 255) -> Surface:
    surface.fill((*color, opacity), special_flags=pg.BLEND_RGBA_MULT)
    return surface

def load_sprite(filename : str, dims : Tuple[int, int] | None = None, color : Color | None = None, opacity : int = 255) -> Surface:
    # filename is path from the sprites file.
    surface = pg.image.load(f'files/sprites/{filename}')

    if dims is not None:
        surface = pg.transform.scale(surface, dims)
    
    if color is not None:
        tint(surface, color, opacity)
    
    return surface


DefaultScheme : Scheme = {
    'tile_white' : (250, 242, 210),
    'tile_black' : (90, 50, 35),

    'player_white' : (220, 192, 180),
    'player_black' : (130, 80, 70),

    'checkmate' : (214, 45, 25),
    'stalemate' : (50, 45, 25),

    'plaque' : (170, 120, 100),
    'text' : (220, 192, 180),

    'select' : (128, 45, 25),
    'see' : (230, 100, 50)
}

IndianScheme : Scheme = {
    'tile_white' : (250, 242, 210),
    'tile_black' : (70, 60, 50),

    'player_white' : (190, 90, 50),
    'player_black' : (90, 190, 50),

    'checkmate' : (214, 45, 25),
    'stalemate' : (50, 45, 25),

    'plaque' : (170, 120, 100),
    'text' : (220, 192, 180),

    'select' : (128, 45, 25),
    'see' : (230, 100, 50)
}

DefaultSFX : SFX = {
    'move' : Sound('files/sounds/move.mp3'), 
    'take' : Sound('files/sounds/take.mp3'), 
    'check' : Sound('files/sounds/check.mp3'), 
    'start' : Sound('files/sounds/start.mp3'), 
    'end' : Sound('files/sounds/end.mp3'),
    'illegal' : Sound('files/sounds/illegal.mp3'),
    'castle' : Sound('files/sounds/castle.mp3'),
    'promote' : Sound('files/sounds/promote.mp3')
}