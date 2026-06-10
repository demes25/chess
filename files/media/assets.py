# Demetre Seturidze
# Chess
# Assets -- Graphics and Sounds

# we create a graphics class - which will hold the necessary graphics throughout an instance of the game.
from typing import Tuple, List, Dict, Callable, Any 
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
def tint(surface : Surface, color : Color, opacity : int = 255) -> Surface:
    surface.fill((*color, opacity), special_flags=pg.BLEND_RGBA_MULT)
    return surface


# wraps a surface to be able to blit/move easier.
# also makes registering hits easier.
#
# by default centers at 0
class Object:
    def __init__(self, surface : Surface, center : Tuple[int, int] = (0, 0)):
        self.surface = surface 
        self.rect = surface.get_rect()
        self.rect.center = center
    
    # returns true if both (or the one given) sets of coordinates collide with this object
    def hits(self, coords : Tuple[int, int], prev_coords : Tuple[int, int] | None = None) -> bool:
        if prev_coords is None:
            return self.rect.collidepoint(coords)
        else:
            return self.rect.collidepoint(coords) and self.rect.collidepoint(prev_coords)
    
    def center_at(self, coords : Tuple[int, int]):
        self.rect.center = coords

    def blit_onto(self, surface : Surface):
        surface.blit(self.surface, self.rect)


class Assets:
    def __init__(
            self, 
            tile_dims : Tuple[int, int], 
            scheme : Scheme = DefaultScheme, 

            asset_dir : Path | str = DEFAULT_ASSET_DIR, 
            sprite_ext = DEFAULT_SPRITE_EXT, 
            sound_ext = DEFAULT_SOUND_EXT, 
            font_ext=DEFAULT_FONT_EXT, 

            sprite_size : float = 0.95,
            
            plaque_opacity : float = 0.8,
            selection_opacity : float = 0.5,

            big_font_size : float = 0.55,
            small_font_size : float = 0.35
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
        
        # figure sprites
        self.tile_width, self.tile_height = w, h = tile_dims
        self.figure_dims = self.figure_width, self.figure_height = sw, sh = sprite_size * w, sprite_size * h

        self.figures : Dict[str, Surface] = dict_from_dir(Path(self.sprite_dir, 'figures'), self.sprite_ext, surface_loader((sw,sh)))

        self.white_tile = tint(self.tiles['Tile'].copy(), scheme['tile_white'])
        self.black_tile = tint(self.tiles['Tile'].copy(), scheme['tile_black'])

        self.white_figures = {
            name : tint(sprite.copy(), scheme['player_white']) for name, sprite in self.figures.items()
        }
        
        self.black_figures = {
            name : tint(sprite.copy(), scheme['player_black']) for name, sprite in self.figures.items()
        }

        self.selected_tile = tint(self.tiles['Tile'].copy(), scheme['select'], opacity=int(selection_opacity * 255))

        font_path = Path(self.asset_dir, f'font.{font_ext}')

        self.big_font = pg.font.Font(font_path, int(big_font_size * h))
        self.small_font = pg.font.Font(font_path, int(small_font_size * h))

        self.sounds : Dict[str, Sound] = dict_from_dir(self.sound_dir, self.sound_ext, func=Sound)

        # constructs a plaque using blocks sprites
        # width and height are the dimensions of the plaque in terms of tiles, 
        # i.e. 3x5 would return a 3 tile by 5 tile plaque    
        class Plaque(Object):
            def __init__(plq, dims : Tuple[int, int], center : Tuple[int, int] = (0, 0), opacity : int = int(plaque_opacity * 255)):
                tile_w, tile_h = self.tile_dims 
                color = self.scheme['plaque']

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
            def __init__(plq, dims : Tuple[int, int], objects : List[Object], center : Tuple[int, int] = (0, 0), opacity : int = int(plaque_opacity * 255)):
                super().__init__(dims=dims, center=center, opacity = opacity)
                plq.objects = objects 

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

            def blit_onto(self, surface : Surface):
                super().blit_onto(surface)

                for obj in self.objects:
                    obj.blit_onto(surface)
                
        self.Plaque = Plaque
        self.ObjectPlaque = ObjectPlaque

    # constructs the game over plaque and necessary objects
    def make_end_plaque(self, label : str, color_name : str | None = None, center : Tuple[int, int] = (0, 0)):
        plaque = self.ObjectPlaque((5, 3), [])

        if color_name is None:
            color_name = label.lower()

        dx_r = plaque.rect.width // 5
        dx_q = plaque.rect.width // 4
        dy = plaque.rect.height // 7

        label_object = Object(self.big_font.render(label, True, self.scheme[color_name]), center=(0, - dy))

        reset_button = Object(self.small_font.render('Reset', True, self.scheme['text']))
        reset_button.rect.center = (dx_r, dy)

        quit_button = Object(self.small_font.render('Quit', True, self.scheme['text']))
        quit_button.rect.center = (-dx_q, dy)

        plaque.objects = [reset_button, quit_button, label_object]

        plaque.center_at(center)

        return plaque 

        
from files.logic.game import Piece 

class AudioVisuals:
    def __init__(self, 
        assets : Assets,
        dimensions : List[int] = [8, 8],
        num_players : int = 2,

        player_index : int = 0 # gives the player index whose perspective we are looking from (0 if white, 1 if black)
    ):
        self.rank = len(dimensions)
        self.num_players = num_players

        self.perspective = player_index

        self.assets = assets
        # TODO: generalize tile dimensions and board rank. right now only supports rank-2 [n x m] boards
        # and 2 players
        assert self.rank == 2
        assert self.num_players == 2

        self.COLS, self.ROWS = self.dimensions = dimensions
        self.width = self.COLS * assets.tile_width
        self.height = self.ROWS * assets.tile_height 

        self.figure_sprites = [assets.white_figures, assets.black_figures]

        board_surface = Surface((self.width, self.height))
        
        tiles = (assets.white_tile, assets.black_tile)
        W = assets.tile_width
        H = assets.tile_height

        for i in range(self.ROWS):
            for j in range(self.COLS):
                # Alternate color based on position
                tile = tiles[(i+j + player_index) % 2]

                board_surface.blit(tile, (j * W, i * H))

        self.board = Object(board_surface)
        self.board.rect.topleft = (0, 0)

        self.selected_piece : Piece | None = None 
        self.hold_selected : bool = False 
        self.selected_squares : List[Object] = [] 

        self.checkmate_plaque = assets.make_end_plaque('Checkmate', center=self.board.rect.center)
        self.stalemate_plaque = assets.make_end_plaque('Stalemate', center=self.board.rect.center)

        class PromotionPlaque(assets.ObjectPlaque):

            from files.logic.figures import Figure 
            def __init__(plq, figures : List[Figure], player_index : int, board_pos : Tuple[int, int]):
                plq.figures = figures
            
                # rudimentary: for now, the default is that the promotion plaque 
                # extends rightwards from the promotion square, unless that clashes with 
                # board dimensions, in which case we go leftwards.
                # TODO: extend this to be able to be a square or some other dimension to accommodate n promotion figures
                # rudimentary: for now, the default is that the promotion plaque 
                # extends rightwards from the promotion square, unless that clashes with 
                # board dimensions, in which case we go leftwards.
                # TODO: extend this to be able to be a square or some other dimension to accommodate n promotion figures
                if (self.dimensions[0]-board_pos[0]) < len(figures):
                    disp = -self.assets.tile_width
                else:
                    disp = self.assets.tile_width
                
                x, y = self.coords(board_pos)
                fx = x
                
                sprites = self.figure_sprites[player_index]
                objects = []
                for fig in figures:
                    sprite = sprites[fig.name]
                    objects.append(Object(sprite, (fx, y)))
                    fx += disp

                plq.width = width = len(figures)
                super().__init__(
                    dims=(width, 1), 
                    objects=objects,
                    center = (x + int(disp*(width -1)/2.0), y)
                )

            # returns the figure which the given coordinates collide with
            def which_hits(plq, coords : Tuple[int, int], prev_coords : Tuple[int, int] | None = None) -> Figure:
                for i in range(plq.width):
                    if plq.objects[i].hits(coords, prev_coords):
                        return plq.figures[i]
                
                return None 

        self.make_promotion_plaque = PromotionPlaque

    # translates a point on the screen to a square on the board
    def board_pos(self, coords : tuple) -> tuple:
        i, j = coords 

        I, J = i // self.assets.tile_width, (self.height - j) // self.assets.tile_height

        if self.perspective == 1:
            J = self.dimensions[1] - J - 1

        return I, J

    # translates a square on the board to its center point on the screen
    def coords(self, board_pos : tuple) -> tuple:
        I, J = board_pos

        if self.perspective == 1:
            J = self.dimensions[1] - J - 1

        i = int(self.assets.tile_width * (I + 0.5))
        j = int(self.height - (J + 0.5)*self.assets.tile_height)

        return i, j 
    

    def select_piece(self, piece : Piece):
        self.selected_piece = piece
        self.hold_selected = True
        if piece is None:
            self.deselect_squares()
        else:
            self.select_square(piece.position)
    
    def select_square(self, position : tuple):
        j, i = position
        w, h = self.assets.tile_dims

        obj = Object(self.assets.selected_tile) 

        if self.perspective == 0:
            i = self.dimensions[1] - i - 1 
        
        obj.rect.topleft = (j * w, i * h)
        self.selected_squares.append(obj) 

    def deselect_piece(self):
        self.selected_piece = None
        self.hold_selected = False 

    def deselect_squares(self):
        self.selected_squares = []


    def play(self, sound_name : str):
        self.assets.sounds[sound_name].play()

    # draws the given game to a surface
    def draw(self, surface : Surface, pieces : List[Dict[int, Piece]], held_coords : Tuple[int, int] | None = None) -> Surface:
        self.board.blit_onto(surface)

        for square in self.selected_squares:
            square.blit_onto(surface)
           
        for piece_dict, sprite_dict in zip(pieces, self.figure_sprites):
            for piece in piece_dict.values():
                sprite = sprite_dict[piece.figure.name]
                if not (piece is self.selected_piece and self.hold_selected):
                    Object(sprite, self.coords(piece.position)).blit_onto(surface)

        if self.selected_piece is not None and self.hold_selected:
            piece = self.selected_piece
            sprite = self.figure_sprites[piece.player.index][piece.figure.name]
            Object(sprite, held_coords).blit_onto(surface)
        
        return surface