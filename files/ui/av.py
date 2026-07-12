# Demetre Seturidze
# Chess
# AudioVisuals

from typing import List, Tuple, Dict, Sequence


from files.media.assets import Assets

from applib import objects
from applib.text import TextEntry, TextRecord
from applib.utils import Color, Coords, Surface, new_surface, Vector, ZERO_VEC, phase

from files.logic.game import Piece 

import pygame as pg


Dimensions = tuple[int | float, int | float]
IntPair = tuple[int, int]

# ALL DIMENSIONS ARE IN TERMS OF TILES!!
# TODO: GENERALIZE

# a wrapper class for audiovisuals given the necessary assets (see Assets).

# BY DEFAULT: the argument 'dims' is in terms of TILES. so dims (5, 4) corresponds to shape (5*tile_width, 4*tile_height)
#             margins are in terms of PIXELS. so margin 5 corresponds to shape (5*pixel_width, 5*pixel_height)
class AudioVisuals:
    def __init__(
        this,
        assets : Assets 
    ):  
        this.assets = assets
        tile_width, tile_height = assets.tile_shape
        
        # The Game Board -- takes care of drawing the board and plaques.
        class GameBoard(objects.Object):
            def __init__(
                self, 
                dims : Sequence[int] = (8, 8), # dimensions of the game board, in tiles
                num_players : int = 2,

                player_index : int = 0, # gives the player index whose perspective we are looking from (0 if white, 1 if black),
                origin : Vector = ZERO_VEC # gives the position of the topleft corner of the board
            ):
                self.rank = len(dims)
                self.num_players = num_players
                self.player_index = player_index

                # TODO: generalize tile dimensions and board rank. right now only supports rank-2 [n x m] boards
                # and 2 players
                assert self.rank == 2
                assert self.num_players == 2

                self.COLS, self.ROWS = self.dims = dims
                super().__init__(assets.tiles_to_coords(dims), origin)

                self.board = self.surface.copy()

                for i in range(self.ROWS):
                    for j in range(self.COLS):
                        # Alternate color based on position
                        tile = assets.colored_tiles[(i+j + player_index) % 2]

                        self.board.blit(tile, assets.tiles_to_coords((j, i)))

                self.selected_piece : Piece | None = None 
                self.hold_selected : bool = False 
                self.selected_squares : List[objects.Object] = [] 


                class PromotionPlaque(objects.Array):
                    from files.logic.figures import Figure 
                    def __init__(plq, figures : List[Figure], player_index : int, board_pos : IntPair, origin : Vector = ZERO_VEC):
                        plq.figures = figures

                        # rudimentary: for now, the default is that the promotion plaque 
                        # extends rightwards from the promotion square, unless that clashes with 
                        # board dimensions, in which case we go leftwards.
                        # TODO: extend this to be able to be a square or some other dimension to accommodate n promotion figures
                        if (self.dims[0]-board_pos[0]) < len(figures):
                            disp = -tile_width
                            left = self.topleft[0] + tile_width * (board_pos[0] - len(figures))
                        else:
                            disp = tile_width
                            left = self.topleft[0] + tile_width * board_pos[0]

                        plaque = assets.make_plaque(
                            shape=(len(figures) * tile_width, tile_height),
                            small_corners=True
                        )

                        super().__init__(
                            plaque, 
                            origin = origin
                        )
                        
                        sprites = assets.colored_figures[player_index]
                        
                        x = 0
                        for fig in figures:
                            sprite = sprites[fig.name]
                            
                            object = objects.Object(sprite)
                            plq.append(object)

                            object.topleft = (x, 0)
                            x += disp
                        
                        plq.topleft = (
                            left,
                            self.topleft[1]
                        )


                self.make_promotion_plaque = PromotionPlaque
                
            # translates a point on the screen to a square on the board
            # if offset is true, takes into account that topleft may not be (0, 0).
            # otherwise treats as if topleft if (0, 0)
            #
            # usually we'd use offset = False for internal operations, offset = True for external ones
            def board_pos(self, coords : Coords, offset = True) -> Sequence[int]:
                i, j = coords 
                
                if offset:
                    i -= (self.origin[0] + self.topleft[0])
                    j -= (self.origin[1] + self.topleft[1])

                I, J = i // tile_width, (self.height - j) // tile_height

                if self.player_index == 1:
                    J = self.dims[1] - J - 1

                return I, J

            # translates a square on the board to its center point on the screen
            # if offset is true, takes into account that topleft may not be (0, 0).
            # otherwise treats as if topleft if (0, 0)
            #
            # usually we'd use offset = False for internal operations, offset = True for external ones
            def coords(self, board_pos : Sequence[int], offset = True, center_point = False) -> Coords:
                I, J = board_pos

                if self.player_index == 1:
                    J = self.dims[1] - J - 1

                if center_point:
                    I += 0.5
                    J += 0.5
                else:
                    J += 1.0

                i = int(tile_width * I)
                j = int(self.height - J*tile_height)

                if offset:
                    i += (self.origin[0] + self.topleft[0])
                    j += (self.origin[1] + self.topleft[1])

                return i, j 
            

            def select_piece(self, piece : Piece | None):
                if piece is not None:
                    self.selected_piece = piece
                    self.selected_sprite = objects.Object(assets.colored_figures[piece.player.index][piece.figure.name])
                    
                    self.select_square(piece.position)
                    self.hold_selected = True
                else:
                    self.deselect_squares()
            
            def select_square(self, position : Sequence[int]):
                j, i = position
                w, h = assets.tile_shape 

                obj = objects.Object(assets.selected_tile) 

                if self.player_index == 0:
                    i = self.dims[1] - i - 1 
                
                obj.rect.topleft = (j * w, i * h)
                self.selected_squares.append(obj) 

            def deselect_piece(self):
                self.selected_piece = None
                self.selected_sprite = None
                self.hold_selected = False 

            def deselect_squares(self):
                self.selected_squares = []

            def play(self, sound_name : str):
                assets.sounds[sound_name].play()

            # draws the given game to a surface
            def draw(self, pieces : List[Dict[int, Piece]]) -> Surface:
                self.surface.blit(self.board.copy(), (0, 0))

                for square in self.selected_squares:
                    square.blit_onto(self.surface)
                
                for piece_dict, sprite_dict in zip(pieces, assets.colored_figures):
                    for piece in piece_dict.values():
                        sprite = sprite_dict[piece.figure.name]
                        if not (piece is self.selected_piece and self.hold_selected):
                            self.surface.blit(sprite, self.coords(piece.position, offset=False, center_point=False))
                
                return self.surface
                           

        # The Timer -- a clock, basically
        class Timer(objects.Object):
            def __init__(
                self,
                margin : int = 3,
                player_index : int = 0,

                origin : Vector = ZERO_VEC
            ):
                clock_color = assets.scheme.tiles[player_index]
                num_color = assets.scheme.chat_texts[1-player_index]

                self.margins = margins = assets.pixels_to_coords(margin)

                text_shape = (5 * assets.text_font.glyph_width + 4*assets.text_font.gap_size, assets.text_font.glyph_height)
                shape = (
                    text_shape[0] + margins[0] * 2,
                    text_shape[1] + margins[1] * 2
                )

                self.background = assets.make_plaque(shape, small_corners=True, color=clock_color)
                self.margins = margins

                self.num_color = num_color

                self.previous_time = 0

                super().__init__(self.background, origin=origin)


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
                
                time_surface = assets.text_font.render(time_str, self.num_color)

                self.surface = self.background.copy()
                self.surface.blit(time_surface, self.margins)

                return self.surface 
        

        # An array of figures:
        # to represent captured figures.
        class FigureArray(objects.Object):
            def __init__(
                self, 
                
                figures_per_row : int,
                figures_per_col : int,

                margin : int = 4,

                player_index : int = 0,

                plaque_opacity : int = 64,
                player_opacity : int = 196,

                origin : Vector = ZERO_VEC
            ):
                self.margins = assets.pixels_to_coords(margin)

                self.FIGURES_PER_ROW = figures_per_row
                self.FIGURES_PER_COL = figures_per_col

                shape = (
                    int(self.margins[0] * 2 + figures_per_row*assets.captured_fig_shape[0]), 
                    int(self.margins[1] * 2 + figures_per_col*assets.captured_fig_shape[1])
                )

                self.background = assets.make_raw_plaque(shape=shape)

                plaque_tint = phase(self.background, color=assets.scheme.plaque.new_opacity(plaque_opacity))
                player_tint = phase(self.background, color=assets.scheme.players[player_index].new_opacity(player_opacity))
                
                self.background.blit(plaque_tint, (0,0))
                self.background.blit(player_tint, (0,0))

                self.INIT_X = self.margins[0]
                self.MAX_X = self.INIT_X + (figures_per_row-1)*assets.captured_fig_shape[0]

                super().__init__(self.background, origin)


            # pieces: list of [player_index, piece_name]
            def draw(self, pieces : List[Tuple[int, str]] | None = None):
                self.surface = self.background.copy()

                CURR_Y = self.margins[1]
                CURR_X = self.INIT_X
                
                if pieces:
                    for player, piece_name in pieces:
                        obj = assets.colored_capt_figs[player][piece_name]
                        self.surface.blit(obj, (CURR_X, CURR_Y))

                        CURR_X += (assets.captured_fig_shape[0])
                        
                        if CURR_X > self.MAX_X:
                            CURR_X = self.INIT_X
                            CURR_Y += (assets.captured_fig_shape[1])
                
                return self.surface


        class GameOverPlaque(objects.Environment):
            def __init__(
                self,
                dims : Dimensions = (5, 3),
                label : str = 'checkmate',
                
                label_color : Color | None = None,

                origin : Vector = ZERO_VEC
            ):
                
                plaque = assets.make_plaque(shape=assets.tiles_to_coords(dims))

                super().__init__(plaque, origin=origin)

                if label_color is None:
                    label_color = assets.scheme.__getattribute__(label.lower()) 

                dx_r = self.width // 5
                dx_q = self.width // 4
                dy = self.height // 7

                x, y = self.midpoint

                label_object = objects.Object(assets.title_font.render(label.upper(), label_color))
                label_object.center = (x, y - dy)
                self['label'] = label_object

                reset_button = objects.Object(assets.half_title_font.render('RESET', assets.scheme.text))
                reset_button.rect.center = (x + dx_r, y + dy)
                self['reset'] = reset_button

                quit_button = objects.Object(assets.half_title_font.render('QUIT', assets.scheme.text))
                quit_button.rect.center = (x-dx_q, y + dy)
                self['quit'] = quit_button


        class GameSideBar(objects.Environment):
            def __init__(
                self,
                
                env_height : int,

                figures_per_row : int = 8,
                figures_per_col : int = 2,

                arr_margin : int = 4,
                clock_margin : int = 3,

                margin : int = 4,

                color : Color = assets.scheme.plaque,

                player_index : int = 0, # the player whose perspective we are on
                
                origin : Vector = ZERO_VEC
            ):  

                self.arrs = tuple( 
                    FigureArray(
                        figures_per_row=figures_per_row,
                        figures_per_col=figures_per_col,
                        margin=arr_margin,
                        player_index = i
                    ) for i in range(2)
                )

                self.clocks = tuple(
                    Timer(clock_margin, player_index=i) for i in range(2)
                )


                self.margins = assets.pixels_to_coords(margin)

                arr_shape = self.arrs[0].shape 
                clock_shape = self.clocks[0].shape 

                env_w = arr_shape[0] + 2 * self.margins[0]
                env_h = env_height

                assert (env_h >= 2 * (3*self.margins[1] + arr_shape[1] + clock_shape[1]))
                assert (env_w >= (clock_shape[0] + 2*self.margins[0]))

                surface = new_surface((env_w, env_h))
                surface.fill(color.rgb)

                super().__init__(surface, origin=origin)

                self.background = surface

                X, Y = self.midpoint

                margin_y = self.margins[1]
                clock_midpt_y = self.clocks[0].midpoint[1]

                clock_center_disp = margin_y + clock_midpt_y
                sign = 1 if player_index == 0 else -1

                signed_clock_disp = sign * clock_center_disp 
                
                arr_center_disp = 2* margin_y + arr_shape[1]//2 + clock_shape[1]
                signed_arr_disp = sign * arr_center_disp

                self.clocks[0].center = (X, Y + signed_clock_disp)
                self.clocks[1].center = (X, Y - signed_clock_disp)

                self.arrs[0].center = (X, Y + signed_arr_disp)
                self.arrs[1].center = (X, Y - signed_arr_disp)

                self['white_clock'] = self.clocks[0]
                self['black_clock'] = self.clocks[1]
                self['white_array'] = self.arrs[0]
                self['black_array'] = self.arrs[1]

            
            def draw(self, times_s : List[int], captured_pieces : List[List[Tuple[int, str]]]):
                assert len(times_s) == len(captured_pieces), 'player numbers must match'
                for clock, time_s in zip(self.clocks, times_s):
                    clock.draw(time_s=time_s)
                
                for arr, pieces in zip(self.arrs, captured_pieces):
                    arr.draw(pieces=pieces)

        
        class ChatSideBar(objects.Environment):
            def __init__(
                self,
                
                env_height : int,

                chat_dims : Dimensions = (5, 4),
                entry_dims : Dimensions = (5, 2),

                margin : int = 5,
                text_margin : int = 4,

                color : Color = assets.scheme.plaque,

                player_index : int = 0, # the player whose perspective we are on
                
                origin : Vector = ZERO_VEC
            ):  
                
                self.margins = assets.pixels_to_coords(margin)

                chat_w, chat_h = chat_shape = assets.tiles_to_coords(chat_dims) 
                entry_w, entry_h = entry_shape = assets.tiles_to_coords(entry_dims)

                env_w = max(chat_w, entry_w) + 2 * self.margins[0]
                env_h = env_height

                assert (env_h >= (3 * self.margins[1] + chat_h + entry_h))
                assert (env_w >= (entry_w + 2 * self.margins[0]))

                surface = new_surface((env_w, env_h))
                surface.fill(color.rgba)

                super().__init__(surface, origin=origin)
                
                collective_height = chat_h + self.margins[1] + entry_h 
                top_margin = (env_height - collective_height)/2
                left_margin = self.margins[0]

                chat_topleft = (left_margin, top_margin)
                entry_topleft = (left_margin, top_margin + chat_h + self.margins[1])

                # generalize this
                chat_plaque = assets.make_plaque(shape = chat_shape)
                entry_plaque = assets.make_plaque(shape = entry_shape)

                font = assets.quarter_text_font
                
                self.text_color = assets.scheme.chat_texts[player_index]

                self.text_margins = assets.pixels_to_coords(text_margin)

                chat_view_shape = (chat_shape[0] - 2 * self.text_margins[0], chat_shape[1] - 2*self.text_margins[1])
                entry_view_shape = (entry_shape[0] - 2 * self.text_margins[0], entry_shape[1] - 2*self.text_margins[1])
                
                chat_box = TextRecord(font=font, width=chat_view_shape[0])
                entry_box = TextEntry(font=font, width=entry_view_shape[0], color=self.text_color)
                
                chat_view = objects.View(chat_plaque, chat_box)
                chat_box.topleft = self.text_margins
                chat_view.topleft = chat_topleft

                entry_view = objects.View(entry_plaque, entry_box)
                entry_box.topleft = self.text_margins
                entry_view.topleft = entry_topleft

                self.chat_box = chat_box
                self.entry_box = entry_box

                self['chat'] = chat_view
                self['entry'] = entry_view

        this.GameBoard = GameBoard

        this.Timer = Timer 
        this.FigureArray = FigureArray

        this.GameSideBar = GameSideBar
        this.GameOverPlaque = GameOverPlaque
        this.ChatSideBar = ChatSideBar


def new_window(size : Coords, caption : str | None = None, icon : Surface | objects.Object | None = None):

    pg.display.init()
    if caption is not None:
        pg.display.set_caption(caption)
    if icon is not None:
        if isinstance(icon, objects.Object):
            icon = icon.surface
        pg.display.set_icon(icon)
    return pg.display.set_mode(size=size)
        


AVType = AudioVisuals | Assets | Coords | tuple[float, float] | Dimensions | int | float

def to_AV(obj : AVType):
    if isinstance(obj, AudioVisuals):
        return obj
    if isinstance(obj, Assets):
        return AudioVisuals(assets=obj)
    else:
        return AudioVisuals(assets=Assets(scaling=obj))