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



# Color Schemes
DefaultScheme : Scheme = {
    'tile_white' : (250, 242, 210),
    'tile_black' : (90, 60, 50),

    'player_white' : (220, 192, 180),
    'player_black' : (130, 100, 90),

    'checkmate' : (255, 25, 15),
    'stalemate' : (200, 180, 150),

    'plaque' : (140, 120, 100),
    'text' : (220, 192, 180),

    'select' : (128, 45, 25),
    'see' : (230, 100, 50)
}

IndianScheme : Scheme = {
    'tile_white' : (250, 242, 210),
    'tile_black' : (70, 60, 50),

    'player_white' : (240, 90, 50),
    'player_black' : (90, 190, 50),

    'checkmate' : (255, 25, 15),
    'stalemate' : (200, 180, 150),

    'plaque' : (140, 120, 100),
    'text' : (220, 192, 180),
}


# The GANG

DaniacitaScheme : Scheme = {
    'tile_white' : (179, 235, 242),
    'tile_black' : (255, 150, 255),

    'player_white' : (64, 224, 208),
    'player_black' : (204, 0, 204),

    'checkmate' : (255, 25, 255),
    'stalemate' : (200, 180, 150),

    'plaque' : (60, 120, 100),
    'text' : (220, 192, 180),
}

CristiancitoScheme : Scheme = {
    'tile_white' : (145, 55, 127),
    'tile_black' : (255, 150, 84),

    'player_white' : (234, 81, 198),
    'player_black' : (255, 100, 26),

    'checkmate' : (255, 25, 15),
    'stalemate' : (200, 180, 150),

    'plaque' : (120, 70, 60),
    'text' : (220, 192, 180),
}

# don't torture Raymah :(
RaymacitaScheme : Scheme = {
    'tile_white' : (255, 176, 212),
    'tile_black' : (7, 51, 99),

    'player_white' : (252, 164, 204),
    'player_black' : (49, 111, 176),

    'checkmate' : (252, 164, 204),
    'stalemate' : (200, 180, 150),

    'plaque' : (53, 97, 143),
    'text' : (220, 192, 180),
}


JoaquitoScheme : Scheme = {
    'tile_white' : (55, 242, 255),
    'tile_black' : (70, 60, 50),

    'player_white' : (190, 90, 50),
    'player_black' : (90, 190, 50),

    'checkmate' : (255, 25, 15),
    'stalemate' : (200, 180, 150),

    'plaque' : (120, 70, 60),
    'text' : (220, 192, 180)
}

LiamcitoScheme : Scheme = {
    'tile_white' : (250, 242, 210),
    'tile_black' : (80, 120, 200),

    'player_white' : (255, 255, 240),
    'player_black' : (100, 149, 237),

    'checkmate' : (100, 180, 255),
    'stalemate' : (200, 180, 150),

    'plaque' : (60, 70, 120),
    'text' : (220, 192, 180)
}


# Sound Effects

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