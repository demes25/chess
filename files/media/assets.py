# Demetre Seturidze
# Chess
# Assets -- Graphics and Sounds

# we create a graphics class - which will hold the necessary graphics throughout an instance of the game.
from typing import Tuple, List, Dict, Callable, Any, Union
from files.media.schemes import Scheme, Color, DefaultScheme
import pygame as pg
from pathlib import Path 

DEFAULT_ASSET_DIR = Path(Path.cwd(), 'files', 'media')

DEFAULT_SOUND_EXT = 'mp3'
DEFAULT_SPRITE_EXT = 'png'
DEFAULT_FONT_EXT = 'ttf'

Sound = pg.mixer.Sound
Surface = pg.surface.Surface 

pg.init()
pg.mixer.init()

# iterates through files of the given extension, yields the file stem name and the path object.
# applies func before yielding if specified
def file_iter(dir : Path, ext : str, func : Callable[[Path], Any] | None = None):
    if func is None:
        for path in Path(dir).glob(f'*.{ext}'):
            yield (path.stem, path)
    else:
        for path in Path(dir).glob(f'*.{ext}'):
            yield (path.stem, func(path))

# iterates through all files with a given extension in the given directory and returns a dictionary of them,
# keyed by the 'stems' (i.e. extensionless names) of the files in question
def dict_from_dir(dir : Path, ext : str, func : Callable[[Path], Any] | None = None):
    return {name : obj for name, obj in file_iter(dir=dir, ext=ext, func=func)}

# creates a blank transparent surface of the given dimensions
def new_surface(dims : Tuple[int, int]):
    return Surface(dims, pg.SRCALPHA)

# returns a function that loads images and scales them to the given dimension
def surface_loader(dims : Tuple[int, int]):
    def _load(path : Path):
        return pg.transform.scale(pg.image.load(path), dims)
    return _load 

# tints an image in-place (and returns)
def tint(surface : Surface, color : Color | None = None, opacity : int = 255) -> Surface:
    if color is not None:
        surface.fill((*color, opacity), special_flags=pg.BLEND_RGBA_MULT)
    return surface


# wraps a surface to be able to blit/move easier.
# also makes registering hits easier.
class Object:
    def __init__(self, surface : Surface, center : Tuple[int, int] | None = None):
        self.surface = surface 
        self.rect = surface.get_rect()
        if center is not None:
            self.rect.center = center
    
    # returns true if both (or the one given) sets of coordinates collide with this object
    def hits(self, coords : Tuple[int, int], prev_coords : Tuple[int, int] | None = None) -> bool:
        if prev_coords is None:
            return self.rect.collidepoint(coords)
        else:
            return self.rect.collidepoint(coords) and self.rect.collidepoint(prev_coords)
    
    def center_at(self, coords : Tuple[int, int]):
        self.rect.center = coords

    def blit_onto(self, dest : Union['Object', Surface]):
        if isinstance(dest, Object):
            dest.surface.blit(self.surface, self.rect)
        else:
            dest.blit(self.surface, self.rect)


class Assets:
    def __init__(
            self, 
            tile_dims : Tuple[int, int], 
            scheme : Scheme = DefaultScheme, 

            asset_dir : Path | str = DEFAULT_ASSET_DIR, 
            sprite_ext = DEFAULT_SPRITE_EXT, 
            sound_ext = DEFAULT_SOUND_EXT, 
            font_ext=DEFAULT_FONT_EXT, 

            plaque_opacity : float = 0.8,
            selection_opacity : float = 0.5,

            sprite_size : float = 0.95,
            captured_sprite_size : float = 0.75, # small sprites, for drawing captures 

            big_title_size : float = 0.55,
            small_title_size : float = 0.35,

            text_size : float = 0.2,
            clock_num_size : float = 0.5625,
        ):

        self.tile_dims = tile_dims
        self.scheme = scheme 

        self.asset_dir = Path(asset_dir) 
        self.sprite_dir = Path(self.asset_dir, 'sprites')
        self.sound_dir = Path(self.asset_dir, 'sounds')

        self.sprite_ext = sprite_ext
        self.sound_ext = sound_ext
        self.font_ext = font_ext

        self.selection_opacity = selection_opacity
        self.plaque_opacity = plaque_opacity

        # blocks with which we can construct plaques 
        self.tiles : Dict[str, Surface] = dict_from_dir(Path(self.sprite_dir, 'tiles'), self.sprite_ext, surface_loader(tile_dims))
        
        
        self.tile_width, self.tile_height = w, h = tile_dims

        # figure sprites
        self.figure_dims = self.figure_width, self.figure_height = sw, sh = sprite_size * w, sprite_size * h
        self.figures : Dict[str, Surface] = dict_from_dir(Path(self.sprite_dir, 'figures'), self.sprite_ext, surface_loader((sw,sh)))
        
        self.captured_figure_dims = self.captured_figure_width, self.captured_figure_height = ssw, ssh = captured_sprite_size * w, captured_sprite_size * h 
        self.captured_figures : Dict[str, Surface] = dict_from_dir(Path(self.sprite_dir, 'figures'), self.sprite_ext, surface_loader((ssw,ssh)))

        self.player_colors = [scheme['player_white'], scheme['player_black']]
        self.tile_colors = [scheme['tile_white'], scheme['player_black']]

        self.colored_tiles : List[Surface] = [tint(self.tiles['Tile'].copy(), color=color) for color in self.tile_colors]
        
        self.colored_figures : List[Dict[str, Surface]] = [
            {
                name : tint(sprite.copy(), color=color) for name, sprite in self.figures.items()
            } for color in self.player_colors
        ]

        self.captured_colored_figures = [
            {
                name : tint(sprite.copy(), color=color) for name, sprite in self.captured_figures.items()
            } for color in self.player_colors
        ]


        self.selected_tile = tint(self.tiles['Tile'].copy(), scheme['select'], opacity=int(selection_opacity * 255))

        # TODO: MAKE BITMAPS INSTEAD OF TTF FILES!!
        title_font_path = Path(self.asset_dir, f'title_font.{font_ext}')

        self.big_title = pg.font.Font(title_font_path, int(big_title_size * h))
        self.small_title = pg.font.Font(title_font_path, int(small_title_size * h))

        self.text_font = pg.font.Font(Path(self.asset_dir, f'text_font.{font_ext}'), int(text_size * h))
        self.clock_font = pg.font.Font(Path(self.asset_dir, f'text_font.{font_ext}'), int(clock_num_size * h))

        self.sounds : Dict[str, Sound] = dict_from_dir(self.sound_dir, self.sound_ext, func=Sound)

        # constructs a plaque using blocks sprites
        # width and height are the dimensions of the plaque in terms of tiles, 
        # i.e. 3x5 would return a 3 tile by 5 tile plaque    
        class Plaque(Object):
            def __init__(plq, dims : Tuple[int, int], center : Tuple[int, int] | None = None, color : Color | None = self.scheme['plaque'], opacity : int = int(plaque_opacity * 255)):
                tile_w, tile_h = self.tile_dims 
    
                plq.width, plq.height = width, height = dims 

                # special cases if any of the dimensions are one
                if width == 1 and height == 1:
                    surface = tint(self.tiles['Single'].copy(), color=color, opacity=opacity)
                
                elif width == 1:
                    surface = new_surface((tile_w, height * tile_h))

                    t = self.tiles['Top']
                    b = self.tiles['Bottom']
                    v = self.tiles['Vertical']

                    surface.blit(t, (0, 0))
                    surface.blit(b, (0, (height-1)*tile_h))

                    for i in range(1, height-1):
                        surface.blit(v, (0, i*tile_h))
                    
                    surface = tint(surface, color=color, opacity = opacity)

                elif height == 1:
                    surface = new_surface((width * tile_w, tile_h))

                    l = self.tiles['Left']
                    r = self.tiles['Right']
                    h = self.tiles['Horizontal']

                    surface.blit(l, (0, 0))
                    surface.blit(r, ((width-1)*tile_w, 0))

                    for i in range(1, width-1):
                        surface.blit(h, (i*tile_w, 0))
                    
                    surface = tint(surface, color=color, opacity = opacity)
                else:
                    surface = new_surface((width * tile_w, height * tile_h))

                    tl = self.tiles['TopLeft']
                    bl = self.tiles['BottomLeft']
                    tr = self.tiles['TopRight']
                    br = self.tiles['BottomRight']

                    BOTTOM = (height-1) * tile_h 
                    RIGHT = (width-1) * tile_w 

                    surface.blit(tl, (0, 0))
                    surface.blit(bl, (0, BOTTOM))
                    surface.blit(tr, (RIGHT, 0))
                    surface.blit(br, (RIGHT, BOTTOM))
                    

                    te = self.tiles['TopEdge']
                    be = self.tiles['BottomEdge']
                    le = self.tiles['LeftEdge']
                    re = self.tiles['RightEdge']
                    
                    for i in range(1, width-1):
                        I = i * tile_w 
                        surface.blit(te, (I, 0))
                        surface.blit(be, (I, BOTTOM))
                    
                    
                    for i in range(1, height-1):
                        I = i * tile_h 
                        surface.blit(le, (0, I))
                        surface.blit(re, (RIGHT, I))
                    
                    
                    m = self.tiles['Middle']
                    for i in range(1, width-1):
                        for j in range(1, height-1):
                            surface.blit(m, (i * tile_w, j * tile_h))
                    
                    
                    surface = tint(surface, color=color, opacity=opacity)

                super().__init__(surface, center=center)


        class ObjectPlaque(Plaque):
            # a plaque that "contains" other objects -- for example, a promotion plaque
            # which contains a list of figures,
            # or a game over plaque which contains buttons -- reset, quit, etc
            #
            # it is taken that the listed objects are positioned wrt to the center of the plaque
            # i.e. -- as if the plaque's center is (0, 0). 
            def __init__(plq, dims : Tuple[int, int], objects : List[Object] | None = None, center : Tuple[int, int] | None = None, color : Color | None = self.scheme['plaque'], opacity : int = int(plaque_opacity * 255)):
                super().__init__(dims=dims, center=center, color=color, opacity=opacity)
                plq.objects = objects or []

            def which_hits(plq, coords : Tuple[int, int], prev_coords : Tuple[int, int] | None = None) -> Object:
                for obj in plq.objects:
                    if obj.hits(coords, prev_coords):
                        return obj 
                    
                return None 
            
            # returns the index in plq.objects of the object that has been hit
            def hit_index(plq, coords : Tuple[int, int], prev_coords : Tuple[int, int] | None = None) -> int:
                for i in range(len(plq.objects)):
                    if plq.objects[i].hits(coords, prev_coords):
                        return i
                    
                return -1
            

            def center_at(plq, coords : Tuple[int, int]):
                x_curr, y_curr = plq.rect.center
                x_next, y_next = plq.rect.center = coords 
                
                dx = x_next - x_curr
                dy = y_next - y_curr

                for object in plq.objects:
                    x, y = object.rect.center 
                    object.rect.center = (x+dx, y+dy)

            def blit_onto(self, dest : Surface | Object):
                super().blit_onto(dest)

                for obj in self.objects:
                    obj.blit_onto(dest)
                
        self.Plaque = Plaque
        self.ObjectPlaque = ObjectPlaque

    # constructs the game over plaque and necessary objects
    def make_end_plaque(self, label : str, color_name : str | None = None, center : Tuple[int, int] = (0, 0)):
        plaque = self.ObjectPlaque(dims=(5, 3), center=(0, 0))

        if color_name is None:
            color_name = label 
        color_name = color_name.lower()

        dx_r = plaque.rect.width // 5
        dx_q = plaque.rect.width // 4
        dy = plaque.rect.height // 7

        label_object = Object(self.big_title.render(label, True, self.scheme[color_name]), center=(0, - dy))

        reset_button = Object(self.small_title.render('Reset', True, self.scheme['text']))
        reset_button.rect.center = (dx_r, dy)

        quit_button = Object(self.small_title.render('Quit', True, self.scheme['text']))
        quit_button.rect.center = (-dx_q, dy)

        plaque.objects = [reset_button, quit_button, label_object]

        plaque.center_at(center)

        return plaque 
