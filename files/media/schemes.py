# Demetre Seturidze
# Chess
# Assets

from typing import Tuple, Dict
from dataclasses import dataclass

Color = Tuple[int, int, int]
Scheme = Dict[str, Color]

GRAYSCALE : Tuple[Color] = (
    (255, 255, 255), # light
    (191, 191, 191), # standard
    (127, 127, 127), # shade
    (64, 64, 64)     # border
)

@dataclass
class Scheme:
    tile_white : Color = (250, 242, 210)
    tile_black : Color = (90, 60, 50)

    player_white : Color = (220, 192, 180)
    player_black : Color = (130, 100, 90)

    text_white : Color = (255, 248, 220)
    text_black : Color = (20, 10, 5)

    checkmate : Color = (255, 25, 15)
    stalemate : Color = (200, 180, 150)

    plaque: Color = (140, 120, 100)
    text : Color = (220, 192, 180)

    select : Color = (128, 45, 25)
    see : Color = (230, 100, 50)


# Color Schemes
DefaultScheme = Scheme()

IndianScheme = Scheme(
    tile_black = (70, 60, 50),

    player_white = (240, 90, 50),
    player_black = (90, 190, 50)
)



# The GANG

DaniacitaScheme = Scheme(
    tile_white = (179, 235, 242),
    tile_black = (255, 150, 255),

    player_white = (64, 224, 208),
    player_black = (204, 0, 204),

    plaque = (60, 120, 100)
)

CristiancitoScheme = Scheme(
    tile_white = (145, 55, 127),
    tile_black = (255, 150, 84),

    player_white = (234, 81, 198),
    player_black = (255, 100, 26),

    plaque = (120, 70, 60),
)

# don't torture Raymah :(
RaymacitaScheme = Scheme(
    tile_white = (255, 176, 212),
    tile_black = (7, 51, 99),

    player_white = (252, 164, 204),
    player_black = (49, 111, 176),

    checkmate = (252, 164, 204),

    plaque = (53, 97, 143)
)


JoaquitoScheme = Scheme(
    tile_white = (55, 242, 255),
    tile_black = (70, 60, 50),

    player_white = (190, 90, 50),
    player_black = (90, 190, 50),

    plaque = (120, 70, 60)
)

LiamcitoScheme = Scheme(
    tile_white = (250, 242, 210),
    tile_black = (80, 120, 200),

    player_white = (255, 255, 240),
    player_black = (100, 149, 237),

    checkmate = (100, 180, 255),
    stalemate = (200, 180, 150),

    plaque = (60, 70, 120)
)

