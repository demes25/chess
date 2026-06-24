# Demetre Seturidze
# Chess
# Assets -- Graphics and Sounds

# we create a graphics class - which will hold the necessary graphics throughout an instance of the game.
from typing import Tuple, List, Dict, Union
from files.media.schemes import Scheme, Color, DefaultScheme
from files.media.fonts import Alphabet, Font
from files.media.utils import Coords, TileCoords, TileIntCoords, Surface, Sound, dict_from_dir, tint, surface_loader, new_surface
import pygame as pg
from pathlib import Path 

DEFAULT_ASSET_DIR = Path(Path.cwd(), 'files', 'media')

DEFAULT_SOUND_EXT = 'mp3'
DEFAULT_SPRITE_EXT = 'png'
DEFAULT_FONT_EXT = 'png'

pg.init()
pg.mixer.init()


# wraps a surface to be able to blit/move easier.
# also makes registering hits easier.
class Object:
    def __init__(self, surface : Surface, center : Coords | None = None):
        self.surface = surface 
        self.rect = surface.get_rect()
        if center is not None:
            self.rect.center = center
    
    # returns true if both (or the one given) sets of coordinates collide with this object
    def hits(self, coords : Coords, prev_coords : Coords | None = None) -> bool:
        if prev_coords is None:
            return self.rect.collidepoint(coords)
        else:
            return self.rect.collidepoint(coords) and self.rect.collidepoint(prev_coords)
    
    def center_at(self, coords : Coords):
        self.rect.center = coords

    def blit_onto(self, dest : Union['Object', Surface]):
        if isinstance(dest, Object):
            dest.surface.blit(self.surface, self.rect)
        else:
            dest.blit(self.surface, self.rect)


class Assets:
    def __init__(
            self, 
            tile_dims : Coords, 
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

            text_size : float = 0.140625,
            clock_num_size : float = 0.5625,
        ):

        self.tile_dims = tile_dims
        self.scheme = scheme 

        self.asset_dir = Path(asset_dir) 
        self.sprite_dir = Path(self.asset_dir, 'sprites')
        self.font_dir = Path(self.sprite_dir, 'fonts')
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

        self.player_colors = [scheme.player_white, scheme.player_black]
        self.tile_colors = [scheme.tile_white, scheme.player_black]
        self.text_colors = [scheme.text_white, scheme.text_black]

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


        self.selected_tile = tint(self.tiles['Tile'].copy(), scheme.select, opacity=int(selection_opacity * 255))


        self.text_alphabet = Alphabet(
            Path(self.font_dir, f'text.{font_ext}')
        )

        self.title_alphabet = Alphabet(
            Path(self.font_dir, f'title.{font_ext}')
        )

        self.big_title = Font(self.title_alphabet, int(big_title_size * h))
        self.small_title = Font(self.title_alphabet, int(small_title_size * h))

        self.text_font = Font(self.text_alphabet, int(text_size * h))
        self.clock_font = Font(self.text_alphabet, int(clock_num_size * h))

        self.sounds : Dict[str, Sound] = dict_from_dir(self.sound_dir, self.sound_ext, func=Sound)

        # constructs a plaque using blocks sprites
        # width and height are the dimensions of the plaque in terms of tiles, 
        # i.e. 3x5 would return a 3 tile by 5 tile plaque    
        class Plaque(Object):
            def __init__(plq, dims : TileIntCoords, center : Coords | None = None, color : Color | None = self.scheme.plaque, opacity : int = int(plaque_opacity * 255)):
                tile_w, tile_h = self.tile_dims 
    
                plq.dims = plq.width, plq.height = width, height = dims

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
            def __init__(plq, dims : TileIntCoords, objects : List[Object] | None = None, center : Coords | None = None, color : Color | None = self.scheme.plaque, opacity : int = int(plaque_opacity * 255)):
                super().__init__(dims=dims, center=center, color=color, opacity=opacity)
                plq.objects = objects or []

            def which_hits(plq, coords : Coords, prev_coords : Coords | None = None) -> Object:
                for obj in plq.objects:
                    if obj.hits(coords, prev_coords):
                        return obj 
                    
                return None 
            
            # returns the index in plq.objects of the object that has been hit
            def hit_index(plq, coords : Coords, prev_coords : Coords | None = None) -> int:
                for i in range(len(plq.objects)):
                    if plq.objects[i].hits(coords, prev_coords):
                        return i
                    
                return -1
            
            def center_at(plq, coords : Coords):
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
        
        
                # a scrollable object, with a view


        class View(Object):
            def __init__(vw, view_dims : TileCoords, scroll_speed : int = 1, reference : Surface | None = None, reference_topleft = (0, 0), center : Coords | None = None):
                vw.view_dims = view_dims
                vw.view_pixels = self.tiles_to_pixels(view_dims)

                vw.scroll_speed = scroll_speed

                # by default, we start with the view at the top-left of the given surface
                vw.MAX_TOP = 0
                vw.MAX_LEFT = 0
                
                vw.MIN_TOP = 0
                vw.MAX_TOP = 0

                vw._left, vw._top = reference_topleft
                
                view_surface = new_surface(vw.view_pixels)
                super().__init__(view_surface, center=center)

                if reference is None:
                    vw.reference = None 
                else:
                    vw.set_reference(reference)


            # restricts the view to be within bounds.
            # returns False if all is well and nothing needed to be corrected,
            # True otherwise
            def restrict(vw) -> bool:
                corrected = False 

                if vw._top > 0:
                    vw._top = 0
                    corrected = True

                if vw._top < vw.MIN_TOP:
                    vw._top = vw.MIN_TOP
                    corrected = True 

                if vw._left > 0:
                    vw._left = 0
                    corrected = True 
                
                if vw._left < vw.MIN_LEFT:
                    vw._left = vw.MIN_LEFT
                    corrected = True 
                
                return corrected

            
            def flip(vw):
                vw.surface = new_surface(vw.view_pixels)
                vw.surface.blit(vw.reference, (vw._left, vw._top))

            def set_reference(vw, reference : Surface):
                vw.reference = reference
                back_rect = reference.get_rect()

                back_width = back_rect.width 
                back_height = back_rect.height 

                vw.MAX_TOP = max(0, vw.rect.height - back_height)
                vw.MAX_LEFT = max(0, vw.rect.width - back_width)
                vw.MIN_TOP = min(-back_height + vw.rect.height, 0)
                vw.MIN_LEFT = min(-back_width + vw.rect.width, 0)

                vw.restrict()
                vw.flip()
            
            # returns True if restrict returns True
            # by defaults restricts the view to be contained within 
            def scroll(vw, dx : int = 0, dy : int = 0, restrict : bool = True) -> bool:
                vw._left -= dx 
                vw._top -= dy 

                corrected = vw.restrict() if restrict else False

                vw.flip()

                return corrected
                
                
                



        self.Plaque = Plaque
        self.ObjectPlaque = ObjectPlaque
        self.View = View

    # constructs the game over plaque and necessary objects
    def make_end_plaque(self, label : str, color : Color | None = None, center : Coords = (0, 0)):
        plaque = self.ObjectPlaque(dims=(5, 3), center=(0, 0))

        if color is None:
            color = self.scheme.__getattribute__(label.lower()) 

        dx_r = plaque.rect.width // 5
        dx_q = plaque.rect.width // 4
        dy = plaque.rect.height // 7

        label_object = Object(self.big_title.render(label.upper(), color), center=(0, - dy))

        reset_button = Object(self.small_title.render('RESET', self.scheme.text))
        reset_button.rect.center = (dx_r, dy)

        quit_button = Object(self.small_title.render('QUIT', self.scheme.text))
        quit_button.rect.center = (-dx_q, dy)

        plaque.objects = [reset_button, quit_button, label_object]

        plaque.center_at(center)

        return plaque 


    # takes from tile-based size to pixel-based size
    def tiles_to_pixels(self, dims : TileCoords | TileIntCoords) -> Coords:
        return (
            int(dims[0] * self.tile_width),
            int(dims[1] * self.tile_height)
        )
    
    # takes from pixel-based size to tile-based size
    def pixels_to_tiles(self, pixels : Coords) -> TileCoords:
        return (
            float(pixels[0])/self.tile_width,
            float(pixels[1])/self.tile_height
        )