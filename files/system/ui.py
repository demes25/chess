# Demetre Seturidze
# Chess
# User Interface

from typing import List, Sequence
from collections.abc import Iterator
from dataclasses import dataclass


from applib import objects
from applib.text import TextEntry, TextRecord
from applib.utils import Color, Coords, Surface, new_surface, Vector, ZERO_VEC, phase
from applib.controls import Controllable, EventUI, Interface

from netlib.serialization import Serializable

from files.media.assets import Assets

from files.engine import Index, Grid, Response, Request, Event 
from files.system.graph import Text, Chat, SystemMessage, UserMessage

import pygame as pg


Dimensions = tuple[int | float, int | float]

# TODO: make CHAT HISTORY communicable.
        
# a wrapper class for audiovisuals given the necessary assets (see Assets).

# BY DEFAULT: the argument 'dims' is in terms of TILES. so dims (5, 4) corresponds to shape (5*tile_width, 4*tile_height)
#             margins are in terms of PIXELS. so margin 5 corresponds to shape (5*pixel_width, 5*pixel_height)
class UserInterface:
    def __init__(
        this,
        assets : Assets 
    ):  
        this.assets = assets
        tile_width, tile_height = assets.tile_shape


        class Piece(objects.Object, Serializable):
            def __init__(
                self,
                name : str,
                position : Index,
                promotion_list : Sequence[str],
                player_index : int
            ):
                self.name = name
                self.player_index = player_index 

                super().__init__(assets.colored_figures[player_index][name])

                self.promotion_list = promotion_list

                self.board_pos = position            


            def resolve_promote(self, index : int):
                self.surface = self.promotion_list[index]
                self.promotion_list = []

            def __setattr__(self, name, value):
                objects.Object.__setattr__(self, name, tuple(value) if name == "board_pos" else value)
            
            # serialization

            def to_dict(self):
                return {
                    "name" : self.name,
                    "position" : self.board_pos,
                    "promotion_list" : self.promotion_list,
                    "player_index" : self.player_index
                }
        

        @dataclass
        class Cache:
            action : tuple[Index, Index]

            start_piece : Piece
            end_piece : Piece | None = None
         

        class Board(objects.Structure, Serializable, Controllable[UserMessage]):    
            def __init__(
                self, 
                dims : Index, # dimensions of the game board, in tiles
                armies : Sequence[list[Piece]], # the pieces involved 
                enforce_player : bool = True
            ):
                self.rank = len(dims)
                self.num_players = len(armies)
                self.player_index = 0

                self.enforce_player = enforce_player

                self.armies = armies

                self.play_sound_if_next_error = True 

                # TODO: generalize tile dimensions and board rank. right now only supports rank-2 [n x m] boards
                # and 2 players
                assert self.rank == 2
                assert self.num_players == 2

                self.COLS, self.ROWS = self.dims = dims
                super().__init__(assets.tiles_to_coords(dims))
                

                self.grid : Grid[Piece] = Grid(dims)

                for army in armies:
                    for piece in army:
                        self._wrap(piece)
                        self.grid[piece.board_pos] = piece
                        piece.topleft = self.coords(piece.board_pos, to_global=False)
                
                self.cache : Cache | None = None

                self.selected_piece : Piece | None = None 
                self.hold_selected : bool = False 
                self.selected_squares : List[objects.Object] = [] 

                self.promotion_plaque : objects.Array | None = None

                self.last_click : Coords | None = None 
                self.end_plaque : objects.Environment | None = None
                





            def __iter__(self) -> Iterator[objects.Object]:
                yield from self.selected_squares
                
                for piece in self.grid:
                    if piece is not self.selected_piece:
                        yield piece
                
                if self.promotion_plaque is not None:
                    yield self.promotion_plaque

                if self.end_plaque is not None:
                    yield self.end_plaque

                if self.selected_piece is not None:
                    yield self.selected_piece
            

            # serialization
            def to_dict(self):
                return {
                    "dims" : self.dims,
                    "armies" : self.armies,
                    "player_index" : self.player_index
                }
            
            def set_player(self, player_index : int):
                self.player_index = player_index

                for i in range(self.ROWS):
                    for j in range(self.COLS):
                        # Alternate color based on position
                        tile = assets.colored_tiles[(i+j + player_index) % self.num_players]

                        self.surface.blit(tile, assets.tiles_to_coords((j, i)))


            def make_promotion_plaque(self, piece : Piece, board_pos : Index):
                figures = piece.promotion_list
                player_index = piece.player_index

                # rudimentary: for now, the default is that the promotion plaque 
                # extends rightwards from the promotion square, unless that clashes with 
                # board dimensions, in which case we go leftwards.
                # TODO: extend this to be able to be a square or some other dimension to accommodate n promotion figures
                if (self.dims[0]-board_pos[0]) < len(figures):
                    disp = -tile_width
                    left = self.topleft[0] + tile_width * (board_pos[0] - len(figures) + 1)
                    x_init = tile_width * (len(figures)-1)
                else:
                    disp = tile_width
                    left = self.topleft[0] + tile_width * board_pos[0]
                    x_init = 0

                plaque = assets.make_plaque(
                    shape=(len(figures) * tile_width, tile_height),
                    small_corners=True
                )

                result = objects.Array(plaque)
                
                sprites = assets.colored_figures[player_index]
                
                x = x_init
                
                for piece in figures:
                    sprite = sprites[piece.name]
                    
                    object = objects.Object(sprite)
                    object.topleft = (x, 0)
                    x += disp

                    result.append(object)

                top = self.top if player_index==self.player_index else self.bottom - tile_height
                
                result.topleft = (
                    left,
                    top
                )

                self._wrap(result)
                self.promotion_plaque = result

            def make_end_plaque(
                self,
                dims : Dimensions = (5, 3),
                label : str = 'checkmate',
                
                label_color : Color | None = None
            ):
                
                plaque = assets.make_plaque(shape=assets.tiles_to_coords(dims))

                result = objects.Environment(plaque)

                if label_color is None:
                    label_color = assets.scheme.__getattribute__(label.lower()) 

                dx_r = result.width // 5
                dx_q = result.width // 4
                dy = result.height // 7

                x, y = result.midpoint

                label_object = objects.Object(assets.title_font.render(label.upper(), label_color))
                label_object.center = (x, y - dy)
                result['label'] = label_object

                reset_button = objects.Object(assets.half_title_font.render('RESET', assets.scheme.text))
                reset_button.rect.center = (x + dx_r, y + dy)
                result['reset'] = reset_button

                quit_button = objects.Object(assets.half_title_font.render('QUIT', assets.scheme.text))
                quit_button.rect.center = (x-dx_q, y + dy)
                result['quit'] = quit_button

                result.center = self.midpoint

                self._wrap(result)
                self.end_plaque = result


            # translates a point on the screen to a square on the board
            # if from_global is true, takes into account that topleft may not be (0, 0).
            # otherwise treats as if topleft if (0, 0)
            #
            # usually we'd use from_global = False for internal operations, from_global = True for external ones
            def board_pos(self, coords : Coords, from_global = True) -> Index:
                i, j = coords 
                
                if from_global:
                    i -= (self.origin[0] + self.topleft[0])
                    j -= (self.origin[1] + self.topleft[1])

                I, J = i // tile_width, (self.height - j) // tile_height

                if self.player_index == 1:
                    J = self.dims[1] - J - 1

                return int(I), int(J)

            # translates a square on the board to its center point on the screen
            # if to_global is true, takes into account that topleft may not be (0, 0).
            # otherwise treats as if topleft if (0, 0)
            #
            # usually we'd use to_global = False for internal operations, to_global = True for external ones
            def coords(self, board_pos : Index, to_global = True, center_point = False) -> Coords:
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

                if to_global:
                    i += (self.origin[0] + self.topleft[0])
                    j += (self.origin[1] + self.topleft[1])

                return int(i), int(j) 
            

        
            # INTERNALS

            def select_piece(self, piece : Piece):
                if piece is not None:
                    self.selected_piece = piece

                    self.select_square(piece.board_pos)
                    self.hold_selected = True
                else:
                    self.deselect_squares()
            
            def select_square(self, position : Index):
                j, i = position

                obj = objects.Object(assets.selected_tile) 

                if self.player_index == 0:
                    i = self.dims[1] - i - 1 
                
                obj.topleft = assets.tiles_to_coords((j, i))
                self._wrap(obj)
                self.selected_squares.append(obj) 

            def unhold_piece(self):
                if self.selected_piece is not None:
                    self.hold_selected = False 
                    self.selected_piece.topleft = self.coords(self.selected_piece.board_pos, to_global=False)

            def deselect_piece(self):
                self.unhold_piece()
                self.selected_piece = None

            def deselect_squares(self):
                self.selected_squares = []

            def play(self, sound_name : str):
                assets.sounds[sound_name].play()

                

            # COMMUNICATION
            
            def _request_move(self, start : Index, end : Index) -> Request:
                action = (start, end)

                start_piece=self.grid[start]
                end_piece=self.grid[end]

                self.cache = Cache(
                    action=action,
                    start_piece=start_piece,
                    end_piece=end_piece
                )

                self.grid[start] = None
                self.grid[end] = start_piece 

                return Request.construct("action", action)

            def _request_promote(self, start_coords : Coords, end_coords : Coords, from_global : bool = True) -> Request | None:
                index = self.promotion_plaque.which_hits(start_coords, end_coords, from_global=from_global)
                if index == -1:
                    return None
                return Request.construct("promote", index)


            def revert_cache(self):
                if self.cache is not None:
                    action = self.cache.action 

                    self.grid[action[0]] = self.cache.start_piece
                    self.grid[action[1]] = self.cache.end_piece

                    self.cache = None
            

            def register_event(self, event : Event) -> tuple[int, Piece] | None:
                result = None 

                self.revert_cache()
                self.deselect_piece()

                sounds : list[str] = []

                actions = event.actions

                __captures = event.die is not None
                __castles = len(actions) > 1

                piece : Piece = self.grid[actions[0][0]]

                if __captures:
                    die = self.grid[event.die]
                    result = (piece.player_index, die)

                    self.armies[die.player_index].remove(die)
                    self.grid[event.die] = None

                    sounds.append("take")

                for action in actions:
                    piece : Piece = self.grid[action[0]]

                    piece.board_pos = action[1]
                    piece.topleft = self.coords(action[1], to_global=False)

                    self.grid[action[0]] = None
                    self.grid[action[1]] = piece

                if event.checks:
                    sounds.append("check")

                if __castles:
                    sounds.append("castle")


                if not (__captures or event.checks or __castles):
                    sounds.append("move")
                
                
                if event.promote is not None:
                    piece.resolve_promote(event.promote)
                    self.promotion_plaque = None

                    sounds.append("promote")
                
                if event.end is not None:
                    self.make_end_plaque(label=event.end)

                    sounds.append("end")
                
                for sound in sounds:
                    self.play(sound)
                
                return result
            
            def register_response(self, response : Response):
                    
                if self.cache is not None and response.label == "promote":
                    self.make_promotion_plaque(
                        self.cache.start_piece, self.cache.action[1]
                    )
                elif response.label == "error":
                    self.revert_cache()
                    
                    if self.play_sound_if_next_error:
                        self.play('illegal')
                        self.deselect_piece()
                    else:
                        self.unhold_piece()

                    print(response.content)
                    self.deselect_squares()
                
                self.play_sound_if_next_error = True


            # CONTROLS

            def _handle_ingame(self, event : EventUI) -> UserMessage | None:
                result = None 

                if event.type == pg.MOUSEBUTTONDOWN:
                    # selects the piece
                    pos = self.board_pos(event.pos)
                    target = self.grid[pos]
                    selected = self.selected_piece

                    overall_condition = target is None or not self.enforce_player or (target.player_index == self.player_index)

                    if overall_condition:
                        if selected is None or (target is not None and target.player_index == selected.player_index):
                            self.deselect_squares()
                            self.select_piece(target)
                        elif target != selected:
                            result = self._request_move(selected.board_pos, pos)
                            self.select_square(pos)    
                            self.deselect_piece()
                            self.play_sound_if_next_error = False 
                
                if event.type == pg.MOUSEBUTTONUP:
                    selected = self.selected_piece

                    if selected is not None:
                        pos = self.board_pos(event.pos)

                        if pos != selected.board_pos:
                            result = self._request_move(selected.board_pos, pos)
                            self.select_square(pos)
                            self.play_sound_if_next_error = True

                        else:
                            self.unhold_piece()
                
                if self.selected_piece is not None and self.hold_selected:
                    self.selected_piece.global_center = pg.mouse.get_pos()

                return result
                    
            def _handle_gameover(self, event : EventUI) -> UserMessage | None:
                result = None
                    
                if event.type == pg.MOUSEBUTTONDOWN:
                    self.last_click = event.pos
                
                if event.type == pg.MOUSEBUTTONUP and self.last_click is not None:
                    button = self.end_plaque.which_hits(event.pos, self.last_click)

                    if button == 'reset': 
                        result = Request.construct(label='reset', content=self.player_index)
                        self.end_plaque = None 

                    elif button == 'quit':
                        result = Request.construct(label='quit', content=self.player_index)
                    
                    self.last_click = None 
                
                return result
            
            def _handle_promotion(self, event : EventUI) -> UserMessage | None:
                result = None

                if event.type == pg.MOUSEBUTTONDOWN:
                    self.last_click = event.pos
                
                if event.type == pg.MOUSEBUTTONUP and self.last_click is not None:
                    result = self._request_promote(event.pos, self.last_click)
                
                return result
            

            def handle(self, event : EventUI, queue : list[UserMessage]): 
                if self.end_plaque is not None:
                    handle = self._handle_gameover
                elif self.promotion_plaque is not None:
                    handle = self._handle_promotion
                else:
                    handle = self._handle_ingame

                result = handle(event)
                if result is not None:
                    queue.append(result)
            

                        
        # The Timer -- a clock, basically
        class Timer(objects.Object):
            def __init__(
                self,
                margin : int = 3,
                player_index : int = 0,
            ):
                clock_color = assets.scheme.tiles[player_index]
                num_color = assets.scheme.chat_texts[1-player_index]

                self.margins = margins = assets.pixels_to_coords(margin)

                text_shape = (5 * assets.text_font.glyph_width + 4*assets.text_font.gap_size, assets.text_font.glyph_height)
                shape = (
                    text_shape[0] + margins[0] * 2,
                    text_shape[1] + margins[1] * 2
                )

                background = assets.make_plaque(shape, small_corners=True, color=clock_color)
                self.margins = margins
                self.time_surface = None

                self.num_color = num_color

                self.previous_time = 0
                self.current_time = 0

                super().__init__(background)

            def set_time(self, time_s : float):
                self.previous_time = self.current_time
                self.current_time = time_s

                if time_s != self.previous_time:
                    rounded_time = round(time_s)
                    minutes =  rounded_time//60
                    assert minutes <= 99 
                    seconds = rounded_time % 60

                    minute_str = f'{minutes}' if minutes >= 10 else f'0{minutes}'
                    second_str = f'{seconds}' if seconds >= 10 else f'0{seconds}'

                    time_str = f'{minute_str}:{second_str}'
                    
                    self.time_surface = assets.text_font.render(time_str, self.num_color)


            def blit_onto(self, dest : Surface | objects.Object):
                if self.time_surface is None:
                    super().blit_onto(dest)
                else:
                    surface = self.surface.copy()
                    surface.blit(self.time_surface, self.margins)

                    if isinstance(dest, objects.Object):
                        dest.surface.blit(surface, self.rect)
                    else:
                        dest.blit(surface, self.rect)

        

        # An array of figures:
        # to represent captured figures.
        #TODO: CONTINUE FROM HERE -- making these intrinsic instead of needing to "draw" each frame.
        # that way everything works under blit_onto. 
        class FigureArray(objects.Array):
            def __init__(
                self, 
                
                figures_per_row : int,
                figures_per_col : int,

                margin : int = 4,

                player_index : int = 0,

                plaque_opacity : int = 64,
                player_opacity : int = 196,
            ):
                self.margins = assets.pixels_to_coords(margin)

                self.FIGURES_PER_ROW = figures_per_row
                self.FIGURES_PER_COL = figures_per_col

                shape = (
                    int(self.margins[0] * 2 + figures_per_row*assets.captured_fig_shape[0]), 
                    int(self.margins[1] * 2 + figures_per_col*assets.captured_fig_shape[1])
                )

                background = assets.make_raw_plaque(shape=shape)

                plaque_tint = phase(background, color=assets.scheme.plaque.new_opacity(plaque_opacity))
                player_tint = phase(background, color=assets.scheme.players[player_index].new_opacity(player_opacity))
                
                background.blit(plaque_tint, (0,0))
                background.blit(player_tint, (0,0))

                self.INIT_X = self.margins[0]
                self.MAX_X = self.INIT_X + (figures_per_row-1)*assets.captured_fig_shape[0]

                self.CURRENT_X = self.INIT_X
                self.CURRENT_Y = self.margins[1]

                super().__init__(background)

            def add(self, piece : Piece | tuple[str, int]):
                if isinstance(piece, Piece):
                    sprite = assets.colored_capt_figs[piece.player_index][piece.name]
                elif isinstance(piece, tuple):
                    name, index = piece
                    sprite = assets.colored_capt_figs[index][name]
                else:
                    raise TypeError(piece.__class__.__name__)
                
                obj = objects.Object(sprite)
                obj.topleft = (self.CURRENT_X, self.CURRENT_Y)
                
                self.CURRENT_X += (assets.captured_fig_shape[0])
                        
                if self.CURRENT_X > self.MAX_X:
                    self.CURRENT_X = self.INIT_X
                    self.CURRENT_Y += (assets.captured_fig_shape[1])

                self.append(obj)


        class SideBar(objects.Environment):
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

            
            def set_times(self, times_s : Sequence[float]):
                for time_s, clock in zip(times_s, self.clocks):
                    clock.set_time(time_s)


            def add(self, player_index : int, piece : Piece | tuple[str, int]):
                self.arrs[player_index].add(piece)

        
        class ChatBar(objects.Environment, Controllable[UserMessage]):
            def __init__(
                self,
                
                env_height : int,

                chat_dims : Dimensions = (5, 4),
                entry_dims : Dimensions = (5, 2),

                margin : int = 5,
                text_margin : int = 4,

                #chat_history : list[tuple[str, int]] | None = None,

                background_color : Color = assets.scheme.plaque,

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
                surface.fill(background_color.rgba)

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
                
                self.player_index = player_index

                self.text_colors = assets.scheme.chat_texts
                self.outgoing_color = self.text_colors[player_index]

                self.text_margins = assets.pixels_to_coords(text_margin)

                chat_view_shape = (chat_shape[0] - 2 * self.text_margins[0], chat_shape[1] - 2*self.text_margins[1])
                entry_view_shape = (entry_shape[0] - 2 * self.text_margins[0], entry_shape[1] - 2*self.text_margins[1])
                
                chat_box = TextRecord(font=font, width=chat_view_shape[0])

                #if chat_history is not None:
                #    for chat, i in chat_history:
                #        chat_box.register(chat, i, color=assets.scheme.chat_texts[i])

                entry_box = TextEntry(font=font, width=entry_view_shape[0], color=self.outgoing_color)
                
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


            def focus(self):
                self.entry_box.show_pointer()

            def defocus(self):
                self.entry_box.hide_pointer()

            def register_text(self, text : Text):
                self.chat_box.register(text.content, color=self.text_colors[text.index])
                
            def register_chat(self, chat : Chat):
                for text in chat.content:
                    self.chat_box.register(text.content, color=self.text_colors[text.index])
            
            def drain(self) -> Text | None:
                content = self.entry_box.clear()

                if content == '':
                    return None
                
                text = Text(
                    content=content,
                    index=self.player_index 
                )

                self.register_text(text)

                return text
            

            def handle(self, event : EventUI, queue : list[UserMessage]):
                result = None 

                if event.type == pg.TEXTINPUT:
                    text = event.text
                    self.entry_box.register(text)
                
                if event.type == pg.KEYDOWN:
                    if event.key == pg.K_BACKSPACE:
                        self.entry_box.backspace()
                    
                    if event.key == pg.K_RETURN:
                        result = self.drain()

                    if event.key == pg.K_LEFT:
                        self.entry_box.move_ptr_left()
                    
                    if event.key == pg.K_RIGHT:
                        self.entry_box.move_ptr_right()
                
                if result is not None:
                    queue.append(result)


        class GameInterface(Interface[UserMessage]):
            def __init__(
                self,
                
                board : Board,

                # TODO: GENERALIZE FOR SIDEBAR SIZES
                player_index : int = 0,
                enforce_player : bool = True 
            ):
                chatbar = ChatBar(env_height = board.shape[1], player_index=player_index)
                statbar = SideBar(env_height = board.shape[1], player_index=player_index)

                board.topleft = chatbar.topright
                statbar.topleft = board.topright

                shape = (
                    chatbar.shape[0] + board.shape[0] + statbar.shape[0],
                    board.shape[1]
                )

                super().__init__(shape)

                ###
                board.set_player(player_index)
                self.board = board
                self.append(board)
                board.enforce_player = enforce_player
                board.play("start")
                ###
                
                self.chatbar = chatbar
                self.append(chatbar)

                self.statbar = statbar
                self.append(statbar)

                self.player_index = player_index
                
                self.text_colors = assets.scheme.chat_texts

                self.running = True

                self.end_plaque = None
                self.promotion_plaque = None 

                self.focus : Controllable | None = None
        

            def set_board(self, board : Board):
                board.set_player(self.player_index)
                board.enforce_player = self.board.enforce_player
                board.topleft = self.board.topleft 

                self.board = self[0] = board
                board.play("start")


            def register(self, msg : SystemMessage | Board):
                if isinstance(msg, Board):
                    self.set_board(msg)
            
                elif isinstance(msg, Response):
                    self.board.register_response(msg)
                    if msg.label == "times":
                        self.statbar.set_times(msg.content)
                
                elif isinstance(msg, Event):
                    result = self.board.register_event(msg)
                    if result is not None:
                        self.statbar.add(*result)

                elif isinstance(msg, Text):
                    self.chatbar.register_text(msg)
                
                elif isinstance(msg, Chat):
                    self.chatbar.register_chat(msg)


            def reset(self, board : Board):
                self.board = board 
                self.promotion_plaque = None 
                self.end_plaque = None 
                self.timeout = False
                self.running = True

            def _quit(self) -> Event:
                self.running = False 
                return Request.construct(label='quit', content=self.player_index)


        # work on making sign-up/login page, etc...
        class EntryInterface(Interface[UserMessage]):
            ...

        this.Piece = Piece
        this.Board = Board

        this.Timer = Timer 
        this.FigureArray = FigureArray

        this.SideBar = SideBar
        this.ChatBar = ChatBar

        this.GameInterface = GameInterface

        this.EntryInterface = EntryInterface


def new_window(size : Coords, caption : str | None = None, icon : Surface | objects.Object | None = None):

    pg.display.init()
    if caption is not None:
        pg.display.set_caption(caption)
    if icon is not None:
        if isinstance(icon, objects.Object):
            icon = icon.surface
        pg.display.set_icon(icon)
    return pg.display.set_mode(size=size)
        


UIType = UserInterface | Assets | Coords | tuple[float, float] | Dimensions | int | float

def to_UI(obj : UIType):
    if isinstance(obj, UserInterface):
        return obj
    if isinstance(obj, Assets):
        return UserInterface(assets=obj)
    else:
        return UserInterface(assets=Assets(scaling=obj))