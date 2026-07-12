# Demetre Seturidze
# Chess
# Assets -- Graphics and Sounds

# we create a graphics class - which will hold the necessary graphics throughout an instance of the game.
from files.media.schemes import Scheme, DefaultScheme
from typing import Sequence

from netlib.filecaster import here

from applib.fonts import Alphabet, Font 
from applib.utils import Coords, Surface, Sound, dict_from_dir, phase, loader, new_surface, scale
from applib.colors import Color

from pathlib import Path 

from pygame.mixer import init

# TODO: move this elsewhere
init()

DEFAULT_ASSET_DIR = here()

DEFAULT_SOUND_EXT = 'mp3'
DEFAULT_SPRITE_EXT = 'png'
DEFAULT_FONT_EXT = 'png'

class Assets:
    def __init__(
            self,  

            asset_dir : Path | str = DEFAULT_ASSET_DIR, 
            
            sprite_ext = DEFAULT_SPRITE_EXT, 
            sound_ext = DEFAULT_SOUND_EXT, 
            font_ext=DEFAULT_FONT_EXT, 

            scaling : int | float | Coords | tuple[float, float] | None = None,
            scheme : Scheme = DefaultScheme
        ):

        # paths
        self.asset_dir = Path(asset_dir) 

        self.sprite_dir = Path(asset_dir, 'sprites')
        self.font_dir = Path(self.sprite_dir, 'fonts')
        self.sound_dir = Path(asset_dir, 'sounds')

        self.sprite_ext = sprite_ext
        self.sound_ext = sound_ext
        self.font_ext = font_ext

        self.load(scaling=scaling, scheme=scheme)


    def _load(self, scaling : int | float | Coords | tuple[float, float] | None = None):

        if scaling is None:
            self.pixel_shape = (1, 1)
        elif isinstance(scaling, tuple):
            self.pixel_shape = scaling
        else:
            self.pixel_shape = (scaling, scaling)

        # loading
        self.loader = loader(scaling=scaling)

        # tiles 
        self.tiles : dict[str, Surface] = dict_from_dir(Path(self.sprite_dir, 'tiles'), self.sprite_ext, self.loader)
        self.plaque_bases : dict[str, Surface] = dict_from_dir(Path(self.sprite_dir, 'plaques'), self.sprite_ext, self.loader)

        # figure sprites
        self.figures : dict[str, Surface] = dict_from_dir(Path(self.sprite_dir, 'figures'), self.sprite_ext, self.loader)
        self.captured_figs : dict[str, Surface] = {
            name : scale(item, 0.5) for name, item in self.figures.items()
        }

        # shapes
        self.tile_shape = self.tiles['Tile'].get_size()
        self.figure_shape = self.figures['Pawn'].get_size()
        self.captured_fig_shape = self.captured_figs['Pawn'].get_size()

        self.plaque_large_corner_shape = self.plaque_bases['TopLeft'].get_size()
        self.plaque_small_corner_shape = self.plaque_bases['TopLeftSmall'].get_size()

        self.plaque_horiz_margin_shape = self.plaque_bases['Left'].get_size()
        self.plaque_vert_margin_shape = self.plaque_bases['Top'].get_size()

        self.plaque_body_shape = self.plaque_bases['Body'].get_size()


        # fonts
        self.text_alphabet = Alphabet(
            Path(self.font_dir, f'text.{self.font_ext}')
        )

        self.title_alphabet = Alphabet(
            Path(self.font_dir, f'title.{self.font_ext}')
        )   
        
        if scaling:
            height_scaling = scaling[1] if isinstance(scaling, tuple) else scaling
        
            title_height = self.title_alphabet.glyph_height * height_scaling
            text_height = self.text_alphabet.glyph_height * height_scaling
        else:
            title_height = self.title_alphabet.glyph_height
            text_height = self.text_alphabet.glyph_height

        self.title_font = Font(self.title_alphabet, int(title_height))
        self.text_font = Font(self.text_alphabet, int(text_height))

        self.half_title_font = Font(self.title_alphabet, int(title_height / 2))
        self.half_text_font = Font(self.text_alphabet, int(text_height / 2))

        self.quarter_text_font = Font(self.text_alphabet, int(text_height / 4))

        # sounds
        self.sounds : dict[str, Sound] = dict_from_dir(self.sound_dir, self.sound_ext, func=Sound)
    
    def set_scheme(self, scheme : Scheme = DefaultScheme):
        self.scheme = scheme

        self.colored_figures : tuple[dict[str, Surface], dict[str, Surface]] = tuple(
            {
                name : phase(img, color) for name, img in self.figures.items()
            } for color in scheme.players
        )

        self.colored_capt_figs : tuple[dict[str, Surface], dict[str, Surface]] = tuple(
            {
                name : phase(img, color) for name, img in self.captured_figs.items()
            } for color in scheme.players
        )

        self.colored_tiles : tuple[Surface, Surface] = tuple(
            phase(self.tiles['Tile'], color) for color in scheme.tiles
        )

        self.selected_tile = phase(self.tiles['Tile'], scheme.select)


    def load(self, scaling : int | float | Coords | tuple[float, float] | None = None, scheme : Scheme = DefaultScheme):
        self._load(scaling=scaling)
        self.set_scheme(scheme=scheme)

    def make_raw_plaque(self, shape : Coords, small_corners : bool = False) -> Surface:
        w, h = shape

        corner_w, corner_h = self.plaque_small_corner_shape if small_corners else self.plaque_large_corner_shape

        assert w >= 3*corner_w
        assert h >= 3*corner_h

        result = new_surface(shape)

        # get margins

        x_margin, x_margin_step = self.plaque_horiz_margin_shape
        y_margin_step, y_margin = self.plaque_vert_margin_shape

        margin_w, margin_h = w - 2*corner_w, h - 2*corner_h

        # blit the body

        body_w, body_h = w - 2*x_margin, h - 2*y_margin

        body = new_surface((body_w, body_h))

        body_sprite = self.plaque_bases['Body']

        body_step_w, body_step_h = self.plaque_body_shape

        for x in range(0, body_w, body_step_w):
            for y in range(0, body_h, body_step_h):
                body.blit(body_sprite, (x,y))

        result.blit(body, (x_margin, y_margin))

        # blit the corners
        if small_corners:
            topleft_sprite = self.plaque_bases['TopLeftSmall']
            topright_sprite = self.plaque_bases['TopRightSmall']
            bottomright_sprite = self.plaque_bases['BottomRightSmall']
            bottomleft_sprite = self.plaque_bases['BottomLeftSmall']
        else:
            topleft_sprite = self.plaque_bases['TopLeft']
            topright_sprite = self.plaque_bases['TopRight']
            bottomright_sprite = self.plaque_bases['BottomRight']
            bottomleft_sprite = self.plaque_bases['BottomLeft']
        
        r = shape[0] - corner_w
        b = shape[1] - corner_h

        result.blit(topleft_sprite, (0, 0))
        result.blit(topright_sprite, (r, 0))
        result.blit(bottomleft_sprite, (0, b))
        result.blit(bottomright_sprite, (r, b))


        # blit the margins
        left_margin = new_surface((x_margin, margin_h))
        right_margin = left_margin.copy()

        top_margin = new_surface((margin_w, y_margin))
        bottom_margin = top_margin.copy()

        left_margin_sprite = self.plaque_bases['Left']
        right_margin_sprite = self.plaque_bases['Right']
        top_margin_sprite = self.plaque_bases['Top']
        bottom_margin_sprite = self.plaque_bases['Bottom']

        for y in range(0, margin_h, y_margin_step):
            left_margin.blit(left_margin_sprite, (0, y))
            right_margin.blit(right_margin_sprite, (0, y))

        for x in range(0, margin_w, x_margin_step):
            top_margin.blit(top_margin_sprite, (x, 0))
            bottom_margin.blit(bottom_margin_sprite, (x, 0))

        r = shape[0] - x_margin
        b = shape[1] - y_margin

        result.blit(top_margin, (corner_w, 0))
        result.blit(left_margin, (0, corner_h))
        result.blit(bottom_margin, (corner_w, b))
        result.blit(right_margin, (r, corner_h))

        return result
        
    def make_plaque(self, shape : Coords, small_corners : bool = False, color : Color | str = 'translucent_plaque') -> Surface:
        result = self.make_raw_plaque(shape=shape, small_corners=small_corners)
        if isinstance(color, str):
            color = getattr(self.scheme, color)
        return phase(result, color, copy=False)
    

    def tiles_to_coords(self, tiles : Sequence[int | float] | int | float) -> Coords:
        if isinstance(tiles, (tuple, list)):
            return tuple(
                int(tiles[i] * self.tile_shape[i]) for i in range(len(tiles))
            )
        else:
            return tuple(
                int(tiles * tile_side) for tile_side in self.tile_shape
            )

    def pixels_to_coords(self, pixels : Sequence[int] | int) -> Coords:
        if isinstance(pixels, (tuple, list)):
            return tuple(
                int(pixels[i] * self.pixel_shape[i]) for i in range(len(pixels))
            )
        else:
            return tuple(
                int(pixels * pixel_side) for pixel_side in self.pixel_shape
            )


    
    

        







        