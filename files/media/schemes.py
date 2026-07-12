# Demetre Seturidze
# Chess
# Assets

from typing import Tuple
from dataclasses import dataclass, field
from applib.colors import Color

GRAYSCALE : Tuple[Color, Color, Color, Color] = (
    Color.from_hex('#FFFFFF'), # light
    Color.from_hex('#BFBFBF'), # standard
    Color.from_hex('#7F7F7F'), # shade
    Color.from_hex('#404040')  # border
)

@dataclass
class Scheme:
    tiles : Tuple[Color, Color] = (
        Color.from_hex('#FAF2D2'),
        Color.from_hex('#5A3C32')
    )

    players : Tuple[Color, Color] = (
        Color.from_hex('#DCC0B4'),
        Color.from_hex('#82645A')
    )

    chat_texts : Tuple[Color, Color] = (
        Color.from_hex('#FAF2D2'),
        Color.from_hex('#322319')
    )

    checkmate : Color = Color.from_hex("#DE170C")
    stalemate : Color = Color.from_hex('#C8B496')
    timeout : Color = Color.from_hex('#DCC0B4')
    
    plaque : Color = Color.from_hex('#8C7864')
    text : Color = Color.from_hex('#DCC0B4')

    select : Color = Color.from_hex('#CD643288')

    translucent_plaque : Color | None = None

    plaque_opacity : int = 200

    def __post_init__(self):
        self.translucent_plaque : Color = self.plaque.new_opacity(self.plaque_opacity)



# Color Schemes
DefaultScheme = Scheme()

IndianScheme = Scheme(
    tiles = (
        Color.from_hex('#FAF2D2'),
        Color.from_hex('#463C32')
    ),

    players = (
        Color.from_hex('#F05A32'),
        Color.from_hex('#5ABE32')
    ),
)


# The GANG

DaniacitaScheme = Scheme(
    tiles = (
        Color.from_hex('#B3EBF2'),
        Color.from_hex('#FF96FF')
    ),
    players = (
        Color.from_hex('#40E0D0'),
        Color.from_hex('#CC00CC')
    ),

    plaque=Color.from_hex('#3C7864')
)

CristiancitoScheme = Scheme(
    tiles = (
        Color.from_hex('#91377F'),
        Color.from_hex('#FF9654')
    ),
    players=(
        Color.from_hex('#EA51C6'),
        Color.from_hex('#FF641A')
    ),

    plaque=Color.from_hex('#78463C')
)

# don't torture Raymah :(
RaymacitaScheme = Scheme(
    tiles=(
        Color.from_hex('#FFB0D4'),
        Color.from_hex('#073363')
    ),

    players=(
        Color.from_hex('#FCA4CC'),
        Color.from_hex('#316FB0')
    ),

    checkmate=Color.from_hex('#FCA4CC'),
    plaque=Color.from_hex('#35618F')
)


JoaquitoScheme = Scheme(
    tiles = (
        Color.from_hex('#37F2FF'),
        Color.from_hex('#463C32')
    ),

    players = (
        Color.from_hex('#BE5A32'),
        Color.from_hex('#5ABE32')
    ),
    
    plaque = Color.from_hex('#78463C')
)

LiamcitoScheme = Scheme(
    tiles = (
        Color.from_hex('#FAF2D2'),
        Color.from_hex('#5078C8')
    ),

    players = (
        Color.from_hex('#FFFFF0'),
        Color.from_hex('#6495ED')
    ),

    checkmate = Color.from_hex('#64B4FF'),
    stalemate = Color.from_hex('#C8B496'),

    plaque = Color.from_hex('#C8B496')
)

