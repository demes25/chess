# Demetre Seturidze
# Chess
# AudioVisuals

from typing import List, Tuple, Dict
from files.media.assets import Object, Assets, Surface, new_surface
from files.logic.game import Piece 


# The Game Board -- takes care of drawing the board and plaques.
class GameBoard(Object):
    def __init__(self, 
        assets : Assets,
        dimensions : List[int] = [8, 8],
        num_players : int = 2,

        player_index : int = 0, # gives the player index whose perspective we are looking from (0 if white, 1 if black),
        topleft : Tuple[int, int] = (0, 0)
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

        self.board = new_surface((self.width, self.height))
        
        super().__init__(new_surface((self.width, self.height)))
        self.rect.topleft = topleft
        
        tiles = (assets.white_tile, assets.black_tile)
        W = assets.tile_width
        H = assets.tile_height

        for i in range(self.ROWS):
            for j in range(self.COLS):
                # Alternate color based on position
                tile = tiles[(i+j + player_index) % 2]

                self.board.blit(tile, (j * W, i * H))

        self.selected_piece : Piece | None = None 
        self.hold_selected : bool = False 
        self.selected_squares : List[Object] = [] 

        self.checkmate_plaque = assets.make_end_plaque('Checkmate', center=self.rect.center)
        self.stalemate_plaque = assets.make_end_plaque('Stalemate', center=self.rect.center)

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
                
                x, y = self.coords(board_pos, offset=False)
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
    # if offset is true, takes into account that topleft may not be (0, 0).
    # otherwise treats as if topleft if (0, 0)
    #
    # usually we'd use offset = False for internal operations, offset = True for external ones
    def board_pos(self, coords : tuple, offset = True) -> tuple:
        i, j = coords 
        
        if offset:
            x, y = self.rect.topleft
            i -= x
            j -= y

        I, J = i // self.assets.tile_width, (self.height - j) // self.assets.tile_height

        if self.perspective == 1:
            J = self.dimensions[1] - J - 1

        return I, J

    # translates a square on the board to its center point on the screen
    # if offset is true, takes into account that topleft may not be (0, 0).
    # otherwise treats as if topleft if (0, 0)
    #
    # usually we'd use offset = False for internal operations, offset = True for external ones
    def coords(self, board_pos : tuple, offset = True) -> tuple:
        I, J = board_pos
        x, y = self.rect.topleft

        if self.perspective == 1:
            J = self.dimensions[1] - J - 1

        i = int(self.assets.tile_width * (I + 0.5))
        j = int(self.height - (J + 0.5)*self.assets.tile_height)

        if offset:
            x, y = self.rect.topleft
            i += x
            y += j 

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
    def draw(self, pieces : List[Dict[int, Piece]], held_coords : Tuple[int, int]) -> Surface:
        self.surface.blit(self.board, (0, 0))

        for square in self.selected_squares:
            square.blit_onto(self.surface)
        
        for piece_dict, sprite_dict in zip(pieces, self.figure_sprites):
            for piece in piece_dict.values():
                sprite = sprite_dict[piece.figure.name]
                if not (piece is self.selected_piece and self.hold_selected):
                    Object(sprite, self.coords(piece.position, offset=False)).blit_onto(self.surface)

        if self.selected_piece is not None and self.hold_selected:
            piece = self.selected_piece
            sprite = self.figure_sprites[piece.player.index][piece.figure.name]
            
            held_x, held_y = held_coords 
            x, y = self.rect.topleft 

            Object(sprite, (held_x-x, held_y-y)).blit_onto(self.surface)
        
        return self.surface
    
