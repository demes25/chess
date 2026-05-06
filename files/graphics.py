# Demetre Seturidze
# Chess
# Color schemes

from typing import Tuple, Dict
import pygame as pg

Color = Tuple[int, int, int]
Scheme = Dict[str, Color]

def load_sprite(filename : str, color : Color, width : int, height : int, opacity : int = 255):
    # Make a copy so original stays unchanged
    surface = pg.image.load(filename)
    surface = pg.transform.scale(surface, (width, height))
    
    # Fill with tint color using multiply blend
    surface.fill((*color, opacity), special_flags=pg.BLEND_RGBA_MULT)
    
    return surface


Default : Scheme = {
    'tile_white' : (250, 242, 210),
    'tile_black' : (90, 50, 35),

    'player_white' : (220, 192, 180),
    'player_black' : (130, 80, 70),

    'checkmate' : (214, 45, 25),
    'stalemate' : (50, 45, 25),

    'game_over' : (170, 120, 100),
    'text' : (220, 192, 180)
}
