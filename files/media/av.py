# Demetre Seturidze
# Chess
# AudioVisuals

from typing import List, Tuple, Dict, Any
from files.media.assets import Object, Assets, Surface, new_surface, tint, Color
from files.logic.game import Piece 
import pygame as pg


# ALL DIMENSIONS ARE IN TERMS OF TILES!!
# TODO: GENERALIZE

# a wrapper class for audiovisuals given the necessary assets (see Assets).
class AudioVisuals:
    def __init__(
        this,
        assets : Assets 
    ):  
        
        # The Game Board -- takes care of drawing the board and plaques.
        class GameBoard(Object):
            def __init__(
                self, 
                dimensions : List[int] = [8, 8], # dimensions of the game board, in tiles
                num_players : int = 2,

                player_index : int = 0, # gives the player index whose perspective we are looking from (0 if white, 1 if black),
                topleft : Tuple[int, int] = (0, 0) # gives the position of the topleft corner of the board
            ):
                self.rank = len(dimensions)
                self.num_players = num_players
                self.player_index = player_index

                # TODO: generalize tile dimensions and board rank. right now only supports rank-2 [n x m] boards
                # and 2 players
                assert self.rank == 2
                assert self.num_players == 2

                self.COLS, self.ROWS = self.dimensions = dimensions
                self.pixel_width = self.COLS * assets.tile_width
                self.pixel_height = self.ROWS * assets.tile_height 

                self.board = new_surface((self.pixel_width, self.pixel_height))
                
                super().__init__(new_surface((self.pixel_width, self.pixel_height)))
                self.rect.topleft = topleft
            
                W = assets.tile_width
                H = assets.tile_height

                for i in range(self.ROWS):
                    for j in range(self.COLS):
                        # Alternate color based on position
                        tile = assets.colored_tiles[(i+j + player_index) % 2]

                        self.board.blit(tile, (j * W, i * H))

                self.figure_sprites = [

                ]

                self.selected_piece : Piece | None = None 
                self.hold_selected : bool = False 
                self.selected_squares : List[Object] = [] 

                self.checkmate_plaque = assets.make_end_plaque('Checkmate', center=self.rect.center)
                self.stalemate_plaque = assets.make_end_plaque('Stalemate', center=self.rect.center)
                self.timeout_plaque = assets.make_end_plaque('Timeout', color_name='stalemate', center=self.rect.center)

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
                            disp = -assets.tile_width
                        else:
                            disp = assets.tile_width
                        
                        x, y = self.coords(board_pos, offset=False)
                        fx = x
                        
                        sprites = assets.colored_figures[player_index]
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

                I, J = i // assets.tile_width, (self.pixel_height - j) // assets.tile_height

                if self.player_index == 1:
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

                if self.player_index == 1:
                    J = self.dimensions[1] - J - 1

                i = int(assets.tile_width * (I + 0.5))
                j = int(self.pixel_height - (J + 0.5)*assets.tile_height)

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
                w, h = assets.tile_dims

                obj = Object(assets.selected_tile) 

                if self.player_index == 0:
                    i = self.dimensions[1] - i - 1 
                
                obj.rect.topleft = (j * w, i * h)
                self.selected_squares.append(obj) 

            def deselect_piece(self):
                self.selected_piece = None
                self.hold_selected = False 

            def deselect_squares(self):
                self.selected_squares = []


            def play(self, sound_name : str):
                assets.sounds[sound_name].play()

            # draws the given game to a surface
            def draw(self, pieces : List[Dict[int, Piece]], held_coords : Tuple[int, int]) -> Surface:
                self.surface.blit(self.board, (0, 0))

                for square in self.selected_squares:
                    square.blit_onto(self.surface)
                
                for piece_dict, sprite_dict in zip(pieces, assets.colored_figures):
                    for piece in piece_dict.values():
                        sprite = sprite_dict[piece.figure.name]
                        if not (piece is self.selected_piece and self.hold_selected):
                            Object(sprite, self.coords(piece.position, offset=False)).blit_onto(self.surface)

                if self.selected_piece is not None and self.hold_selected:
                    piece = self.selected_piece
                    sprite = assets.colored_figures[piece.player.index][piece.figure.name]
                    
                    held_x, held_y = held_coords 
                    x, y = self.rect.topleft 

                    Object(sprite, (held_x-x, held_y-y)).blit_onto(self.surface)
                
                return self.surface

        # The Timer -- a clock, basically
        class Timer(assets.Plaque):
            def __init__(
                self,
                dims : Tuple[int, int] = (3, 1),
                center : Tuple[int, int] = (0,0),
                player_index : int = 0
            ):

                clock_color = assets.tile_colors[player_index]
                num_color = assets.tile_colors[1-player_index]

                super().__init__(dims=dims, center=None, color=clock_color, opacity=255)

                self._center = self.rect.center 

                self.background = self.surface
                self.num_color = num_color

                if center is not None:
                    self.center_at(center)

                self.previous_time = 0

            def draw(self, time_s : float) -> Surface:
                # check if we already printed this time:
                if time_s == self.previous_time:
                    return self.surface 
                
                rounded_time = round(time_s)
                minutes =  rounded_time//60
                assert minutes <= 99 
                seconds = rounded_time % 60

                minute_str = f'{minutes}' if minutes >= 10 else f'0{minutes}'
                second_str = f'{seconds}' if seconds >= 10 else f'0{seconds}'

                time_str = f'{minute_str}:{second_str}'
                
                time_surface = assets.clock_font.render(time_str, True, self.num_color)
                time_rect = time_surface.get_rect()
                time_rect.center = self._center 

                self.surface = self.background.copy()
                self.surface.blit(time_surface, time_rect)

                return self.surface 

        # An array of figures:
        # to represent captured figures.
        class FigureArray(assets.Plaque):
            def __init__(
                self, 
                
                dims : Tuple[int, int],
                center : Tuple[int, int] = (0, 0),

                margin : float = 0.25,

                player_index : int = 0,

                plaque_opacity : int = 64,
                player_opacity : int = 196
            ):
                self.x_margin = int(margin * assets.tile_width)
                self.y_margin = int(margin * assets.tile_height) 

                super().__init__(dims=dims, center=center, color=None, opacity=255)
    
                self.background = self.surface

                plaque_tint = tint(self.surface.copy(), color=assets.scheme['plaque'], opacity=plaque_opacity)
                self.background.blit(plaque_tint, (0,0))
                player_tint = tint(self.surface.copy(), color=assets.player_colors[player_index], opacity=player_opacity)
                self.background.blit(player_tint, (0,0))


            # pieces: list of [player_index, piece_name]
            def draw(self, pieces : List[Tuple[int, str]] = []):
                self.surface = self.background.copy()

                CURR_HEIGHT = self.y_margin + assets.captured_figure_height // 2
                INIT_WIDTH = CURR_WIDTH = self.x_margin + assets.captured_figure_width // 2

                MAX_WIDTH = assets.captured_figure_width * assets.tile_width  - 2*INIT_WIDTH + 3

                for player, piece_name in pieces:
                    obj = Object(assets.captured_colored_figures[player][piece_name], (CURR_WIDTH, CURR_HEIGHT))
                    obj.blit_onto(self.surface)

                    CURR_WIDTH += assets.captured_figure_width
                    
                    if CURR_WIDTH > MAX_WIDTH:
                        CURR_WIDTH = INIT_WIDTH
                        CURR_HEIGHT += assets.captured_figure_height
                
                return self.surface


        class GameSideBar(Object):
            def __init__(
                self,
                arr_dims : Tuple[int, int] = (5, 2),
                clock_dims : Tuple[int, int] = (3, 1),

                env_height : float = 8,
                margin : float = 0.25,

                color : Color = assets.scheme['plaque'],
                #array_dims : Tuple[int, int],

                player_index : int = 0, # the player whose perspective we are on
                
                topleft : Tuple[int, int] = (0, 0)
            ):  
                arr_w, arr_h = arr_dims
                clock_w, clock_h = clock_dims 

                env_w = arr_w + 2 * margin
                env_h = env_height

                self.dims = env_w, env_h

                assert (env_height >= 2 * (margin + arr_h + margin + clock_h + margin))
                assert (env_w > clock_w)

                self.pixel_width, self.pixel_height = pixel_dims = (env_w*assets.tile_width, env_h*assets.tile_height)

                surface = new_surface(pixel_dims)
                surface.fill(color)

                super().__init__(surface)
                self.background = surface
                
                X, Y = self.rect.center # take local center
                self.rect.topleft = topleft # THEN shift the rectangle

                pixel_margin_y = int(margin * assets.tile_height)
                clock_midpt_y = int(clock_h * assets.tile_height/ 2)

                clock_center_disp = pixel_margin_y + clock_midpt_y
                sign = 1 if player_index == 0 else -1

                signed_clock_disp = sign * clock_center_disp 
                
                clock_centers = [(X, Y + signed_clock_disp), (X, Y - signed_clock_disp)]

                arr_center_disp = 2* pixel_margin_y + int((arr_h/2 + clock_h) * assets.tile_height)
                signed_arr_disp = sign * arr_center_disp

                arr_centers = [(X, Y + signed_arr_disp), (X, Y - signed_arr_disp)]
                
                self.clocks = [Timer(clock_dims, center=center, player_index=i) for center, i in zip(clock_centers, range(2))] 
                self.arrs = [FigureArray((arr_w, arr_h), center=center,margin=margin,player_index=i) for center, i in zip(arr_centers, range(2))]

            
            def draw(self, times_s : List[int], captured_pieces : List[List[Tuple[int, str]]]):
                self.surface = self.background.copy()
                
                assert len(times_s) == len(captured_pieces), 'player numbers must match'
                for clock, time_s in zip(self.clocks, times_s):
                    clock.draw(time_s=time_s)
                    clock.blit_onto(self.surface)
                
                for arr, pieces in zip(self.arrs, captured_pieces):
                    arr.draw(pieces=pieces)
                    arr.blit_onto(self.surface)
                
                return self.surface 







                    

        #this.GameSideBar = GameSideBar
        this.GameBoard = GameBoard
        this.Timer = Timer 
        this.FigureArray = FigureArray
        this.GameSideBar = GameSideBar
        


AVType = AudioVisuals | Assets | Tuple[int, int]

def to_AV(obj : AVType):
    if isinstance(obj, AudioVisuals):
        return obj
    if isinstance(obj, Assets):
        return AudioVisuals(assets=obj)
    else:
        return AudioVisuals(assets=Assets(obj))

