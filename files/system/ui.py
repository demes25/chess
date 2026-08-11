# Demetre Seturidze
# Chess
# User Interface

from typing import List, Sequence, Literal
from collections.abc import Iterator
from dataclasses import dataclass


from applib import objects
from applib.text import TextEntry, TextRecord, Font
from applib.utils import Color, Coords, Surface, new_surface, Vector, ZERO_VEC, phase, scale, alpha_blend
from applib.controls import Controllable, EventUI, FocusContainer, Scrollable

from files.media.schemes import GRAYSCALE
from files.media.schemes import CristiancitoScheme

from netlib.serialization import Serializable, deserialize

from files.media.assets import Assets

from files.engine import Index, Grid, EngineResponse, EngineRequest, EngineEvent, EngineError
from files.system.items import Text, SystemResponse, SystemRequest, Layout, Response, Request, Auth, Error, UserLayout, Challenge

import pygame as pg

Dimensions = tuple[int | float, int | float]

AnchorPoint = Literal['center', 'left', 'right']

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

        king_scale : int = 2
        king_color : Color = CristiancitoScheme.players[0]

        text_color : Color = CristiancitoScheme.tiles[0]
        subtext_color : Color = CristiancitoScheme.players[0]

        ### LOGOS AND ICON ###
        king = objects.Object(phase(scale(assets.figures['King'], king_scale), king_color, False))

        scaled_pixel = assets.pixels_to_coords(king_scale)
        icon_shape = (king.width - 2*scaled_pixel[0], king.height - 2*scaled_pixel[1])

        icon = objects.Object(icon_shape)
        icon.surface.blit(king.surface, (-scaled_pixel[0], -scaled_pixel[1]))

        title_font = assets.title_font
        subtitle_font = assets.half_title_font

        _title = phase(title_font.render("OBCHESSED", text_color), GRAYSCALE[1], copy=False)
        _shade = title_font.render("OBCHESSED", subtext_color)

        _subtitle = subtitle_font.render("ONLINE")

        title_shape = _title.get_size()
        title_shape = (title_shape[0] + assets.pixel_shape[0], title_shape[1] + assets.pixel_shape[1])

        title = objects.Object(title_shape)
        title.surface.blit(_shade, (0, 0))
        title.surface.blit(_title, assets.pixel_shape)

        title_plus_subtitle_shape = title_shape[0], title_shape[1] + assets.pixel_shape[1] + _subtitle.get_height()
        title_plus_subtitle = objects.Object(title_plus_subtitle_shape)
        title.blit_onto(title_plus_subtitle)
        subtitle = objects.Object(_subtitle)
        subtitle.center = title_plus_subtitle.center 
        subtitle.bottom = title_plus_subtitle.bottom
        subtitle.blit_onto(title_plus_subtitle)

        logo_shape = (max(title_shape[0], king.width), title_shape[1] + assets.pixel_shape[1] + king.height)
        logo = objects.Object(logo_shape)

        king.center = logo.center
        king.top = logo.top

        title.center = logo.center
        title.bottom = logo.bottom

        king.blit_onto(logo.surface)
        title.blit_onto(logo.surface)

        online_logo_shape = (max(title_plus_subtitle_shape[0], king.width), title_plus_subtitle_shape[1] + assets.pixel_shape[1] + king.height)
        online_logo = objects.Object(online_logo_shape)

        king.center = online_logo.center 
        king.top = online_logo.top

        title_plus_subtitle.center = online_logo.center
        title_plus_subtitle.bottom = online_logo.bottom

        king.blit_onto(online_logo.surface)
        title_plus_subtitle.blit_onto(online_logo.surface)
        ###

        this.icon = icon
        this.logo = logo
        this.online_logo = online_logo




        class InputField(Scrollable[SystemRequest]):
            def __init__(
                self,
                font : Font,
                shape : Coords | int,
                color : Color = assets.scheme.text,
                margin : float = 1,
                velocity : float = 2.0,
                small_corners : bool = False,
                background_color : Color | str = 'translucent_plaque',
                default_text : str | None = None
            ):

                
                margins = assets.pixels_to_coords(margin)
                if isinstance(shape, tuple):
                    entry = TextEntry(font, shape[0] - 2*margins[0], color)
                else:
                    entry = TextEntry(font, shape - 2*margins[0], color)

                if default_text is not None:
                    self.default_text = objects.Object(font.render(default_text, color=color.new_opacity(127)))
                    self.default_text.topleft = margins
                else:
                    self.default_text = None
                
                self.is_in_focus = False
                
                if isinstance(shape, int):
                    shape = (shape, font.glyph_height + 2*margins[1])

                plaque = assets.make_plaque(shape=shape, small_corners=small_corners, color=background_color)
                super().__init__(plaque, item=entry, margins=margins, velocity=velocity)

            def __iter__(self):
                yield self.item

                if not self.is_in_focus and self.default_text is not None and self.item.string == '':
                    yield self.default_text


            def enfocus(self):
                self.item.show_pointer()
                self.is_in_focus = True

            def defocus(self):
                self.item.hide_pointer()
                self.is_in_focus = False

        class Button(objects.Object):
            def __init__(self, text : str, min_width : int = 0, font : Font = assets.half_title_font, color : Color = assets.scheme.text, anchor : AnchorPoint = 'center', margin : float = 3, background_color : Color | str = 'button'):
                text_obj = objects.Object(font.render(text, color))
                margins = assets.pixels_to_coords(margin)
                
                shape = (max(text_obj.width + 2*margins[0], min_width), font.glyph_height + 2*margins[1])
                surface = assets.make_plaque(shape, small_corners=True, color=background_color)

                self.string = text 

                super().__init__(surface)

                if anchor == 'center':
                    text_obj.center = self.midpoint
                elif anchor == 'left':
                    text_obj.topleft = margins
                elif anchor == 'right':
                    text_obj.topright = (self.width - margins[0], margins[1])

                text_obj.blit_onto(self.surface)

                shade = alpha_blend(surface, Color.from_hex("#00000032"))

                self.shaded_surface = self.surface.copy()
                self.shaded_surface.blit(shade, (0, 0))

                self.default_surface = self.surface

            def click(self):
                self.surface = self.shaded_surface
                assets.play_sound('click')
                self.is_clicked = True

            def unclick(self):
                self.surface = self.default_surface
                self.is_clicked = False 

        class Selection(objects.Array, Controllable[SystemRequest]):
            def __init__(self, width : int,  choices : list[str], font : Font, text_color : Color = assets.scheme.text, anchor : AnchorPoint = 'center', margin : float = 3.0, button_color : Color = assets.scheme.button, keep_after_defocus : bool = False):
                choice_buttons : list[Button] = []
                total_height = 0

                self.font = font
                self.text_color = text_color
                self.margin = margin
                self.anchor = anchor
                self.button_color = button_color

                self.selected : Button | None = None
                self._keep_after_defocus = keep_after_defocus

                for choice in choices:
                    new_button = Button(choice, min_width=width, font=font, color=text_color, anchor=anchor, margin=margin, background_color=button_color)
                    if choice_buttons:
                        new_button.topleft = choice_buttons[-1].bottomleft
                    choice_buttons.append(new_button)
                    total_height += new_button.height

                super().__init__((width, max(total_height, 1)))
                self.extend(choice_buttons)

                self.CURRENT_Y = total_height


            def toggle_keep(self):
                self._keep_after_defocus = not self._keep_after_defocus

            def enfocus(self):
                return

            def defocus(self):
                if not self._keep_after_defocus:
                    self.deselect()
            
            def deselect(self):
                if self.selected is not None:
                    self.selected.unclick()
                    self.selected = None

            def select(self, key : int):
                if key == -1:
                    self.deselect()
                else:
                    choice = self[key]

                    if self.selected is not choice:
                        if self.selected is not None:
                            self.selected.unclick()
                        self.selected = choice
                        choice.click()
            
            def handle(self, event : EventUI, _ : list[SystemRequest]):
                if event.type == pg.MOUSEBUTTONDOWN and event.button <= 2:
                    choice = self.which_hits(event.pos)
                    self.select(choice)
                
            def add(self, choice : str):
                new_button = Button(choice, min_width=self.width, font=self.font, color=self.text_color, anchor=self.anchor, margin=self.margin, background_color=self.button_color)

                
                if (self.height - self.CURRENT_Y) < (new_button.height):
                    self._set(new_surface((self.width, self.height + new_button.height)), fixed='topleft')

                new_button.topleft = (0, self.CURRENT_Y)
                self.CURRENT_Y += new_button.height
                self.append(new_button)

            def delete(self, choice : str):
                target_index = None 
                
                for i in range(len(self)):
                    if self[i].string == choice:
                        target_index = i
                        break

                if target_index is None:
                    return

                o = self[target_index]
                shift_amount = o.height
                self.remove(o)

                for j in range(target_index, len(self)):
                    self[j].top -= shift_amount

        class ScrollableSelection(Scrollable[SystemRequest]):
            def __init__(self, shape : Coords,  choices : list[str], font : Font, text_color : Color = assets.scheme.text, anchor : AnchorPoint = 'center', view_margin : float = 3.0, text_margin : float = 3.0, button_color : Color = assets.scheme.button, background_color : Color = assets.scheme.plaque, keep_after_defocus : bool = False):

                margins = assets.pixels_to_coords(view_margin)
                width = shape[0] - 2*margins[0]

                selection = Selection(width, choices=choices, font=font, text_color=text_color, anchor=anchor, margin=text_margin, button_color=button_color, keep_after_defocus=keep_after_defocus)
                plaque = assets.make_plaque(shape, small_corners=True, color=background_color)

                super().__init__(plaque, item=selection, margins=margins)

            def add(self, choice : str):
                self.item.add(choice)

            def delete(self, choice : str):
                self.item.delete(choice)



               
               
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
                self.surface = assets.colored_figures[self.player_index][self.promotion_list[index]]
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
         

        class Board(objects.Structure, Serializable, Controllable[SystemRequest]):    
            def __init__(
                self, 
                dims : Index, # dimensions of the game board, in tiles
                armies : Sequence[list[Piece]], # the pieces involved 
                enforce_player : bool = True
            ):
                self.rank = len(dims)
                self.num_players = len(armies)
                self.player_index = None 

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
                
                self.cache : Cache | None = None

                self.selected_piece : Piece | None = None 
                self.hold_selected : bool = False 
                self.selected_squares : List[objects.Object] = [] 

                self.promotion_plaque : objects.Array | None = None

                self.last_click : Coords | None = None 
                self.end_plaque : objects.Mapping | None = None
                





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
                    "enforce_player" : self.enforce_player
                }
            
            def set_player(self, player_index : int):
                self.player_index = player_index

                for i in range(self.ROWS):
                    for j in range(self.COLS):
                        # Alternate color based on position
                        tile = assets.colored_tiles[(i+j + player_index) % self.num_players]

                        self.surface.blit(tile, assets.tiles_to_coords((j, i)))

                for army in self.armies:
                    for piece in army:
                        piece.topleft = self.coords(piece.board_pos, to_global=False)


            def make_promotion_plaque(self, piece : Piece, board_pos : Index):
                figures = piece.promotion_list
                player_index = piece.player_index

                # rudimentary: for now, the default is that the promotion plaque 
                # extends rightwards from the promotion square, unless that clashes with 
                # board dimensions, in which case we go leftwards.
                # TODO: extend this to be able to be a square or some other dimension to accommodate n promotion figures
                if (self.dims[0]-board_pos[0]) < len(figures):
                    disp = -tile_width
                    left = tile_width * (board_pos[0] - len(figures) + 1)
                    x_init = tile_width * (len(figures)-1)
                else:
                    disp = tile_width
                    left = tile_width * board_pos[0]
                    x_init = 0

                plaque = assets.make_plaque(
                    shape=(len(figures) * tile_width, tile_height),
                    small_corners=True
                )

                result = objects.Array(plaque)
                
                sprites = assets.colored_figures[player_index]
                
                x = x_init
                
                for piece in figures:
                    sprite = sprites[piece]
                    
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

                result = objects.Mapping(plaque)

                if label_color is None:
                    if not hasattr(assets.scheme, label.lower()):
                        label_color = assets.scheme.draw
                    else:
                        label_color = getattr(assets.scheme, label.lower()) 

                
                x, y = result.midpoint

                close_center = x // 2 
                reset_center = (x * 3 ) // 2
                dy = result.height // 7

                label_object = objects.Object(assets.title_font.render(label.upper(), label_color))
                label_object.center = (x, y - dy)
                result['label'] = label_object

                reset_button = Button('RESET', background_color=assets.scheme.plaque)
                reset_button.rect.center = (reset_center, y + dy)
                result['reset'] = reset_button

                close_button = Button('CLOSE', background_color=assets.scheme.plaque)
                close_button.rect.center = (close_center, y + dy)
                result['close'] = close_button

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

            def deselect_piece(self, unhold = True):
                if unhold:
                    self.unhold_piece()
                self.selected_piece = None

            def deselect_squares(self):
                self.selected_squares = []

                

            # COMMUNICATION
            
            def _request_move(self, start : Index, end : Index) -> EngineRequest:
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

                return EngineRequest.construct("action", action)

            def _request_promote(self, start_coords : Coords, end_coords : Coords, from_global : bool = True) -> EngineRequest | None:
                index = self.promotion_plaque.which_hits(start_coords, end_coords, from_global=from_global)
                if index == -1:
                    return None
                return EngineRequest.construct("promotion", index)


            def revert_cache(self):
                if self.cache is not None:
                    action = self.cache.action 

                    self.grid[action[0]] = self.cache.start_piece
                    self.grid[action[1]] = self.cache.end_piece

                    self.cache = None
            

            def register_event(self, event : EngineEvent) -> tuple[int, Piece] | None:
                result = None 

                self.revert_cache()
                self.deselect_piece()
                self.deselect_squares()

                sounds : list[str] = []

                actions = event.actions

                __captures = event.die is not None
                __castles = len(actions) > 1

                piece : Piece = self.grid[actions[0][0]]

                self.select_square(actions[0][0])
                self.select_square(actions[0][1])

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

                    self.deselect_piece()
                    self.deselect_squares()

                    sounds.append("end")
                
                for sound in sounds:
                    assets.play_sound(sound)
                
                return result
            
            def register_response(self, response : EngineResponse):
                if self.cache is not None and response.label == "promote":
                    self.make_promotion_plaque(
                        self.cache.start_piece, self.cache.action[1]
                    )

                    self.deselect_piece(unhold=False)

                elif response.label in ("timeout", "abandonment", "draw"):
                    self.make_end_plaque(label=response.label)
                    self.deselect_piece()
                    self.deselect_squares()
                    assets.play_sound("end")

            def register_error(self, err : EngineError):
                if self.cache is not None and err.label == "InGame":
                    self.revert_cache()
                    
                    if self.play_sound_if_next_error:
                        assets.play_sound('illegal')

                    self.deselect_piece()
                    self.deselect_squares()

                    print(err.content)
                    self.play_sound_if_next_error = True



            # CONTROLS

            def _handle_ingame(self, event : EventUI) -> SystemRequest | None:
                result = None 

                if event.type == pg.MOUSEBUTTONDOWN and event.button <= 2:
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
                
                if event.type == pg.MOUSEBUTTONUP and event.button <= 2:
                    selected = self.selected_piece

                    if selected is not None:
                        if not self.hits(event.pos):
                            self.unhold_piece()
                        else:
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
                    
            def _handle_gameover(self, event : EventUI) -> SystemRequest | None:
                result = None

                # this is good mouse design. this should happen for other things also.     
                if event.type == pg.MOUSEBUTTONDOWN and event.button <= 2:
                    self.last_click = event.pos
                    button = self.end_plaque.which_hits(event.pos)

                    if button in ('reset', 'close'):
                        self.end_plaque[button].click()

                
                if event.type == pg.MOUSEBUTTONUP and event.button <= 2 and self.last_click is not None:
                    button = self.end_plaque.which_hits(event.pos, self.last_click)

                    if button in ('reset', 'close'):
                        result = Request(label=button, content=self.player_index)
                        self.end_plaque[button].unclick()

                    if button == 'reset':
                        self.end_plaque = None 
                    
                    self.last_click = None 
                
                return result
            
            def _handle_promotion(self, event : EventUI) -> SystemRequest | None:
                result = None

                if event.type == pg.MOUSEBUTTONDOWN and event.button <= 2:
                    self.last_click = event.pos
                
                if event.type == pg.MOUSEBUTTONUP and event.button <= 2 and self.last_click is not None:
                    result = self._request_promote(event.pos, self.last_click)
                
                return result
            

            def handle(self, event : EventUI, queue : list[SystemRequest]): 
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
                margin : float = 3,
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

                if time_s != self.previous_time and time_s >= 0:
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
        class FigureArray(Scrollable[SystemRequest]):
            def __init__(
                self, 
                
                figures_per_row : int,
                figures_per_col : int,

                margin : float = 4,

                player_index : int = 0,

                plaque_opacity : int = 64,
                player_opacity : int = 196,
            ):
                margins = assets.pixels_to_coords(margin)

                self.FIGURES_PER_ROW = figures_per_row
                self.FIGURES_PER_COL = figures_per_col

                inter_width = figures_per_row*assets.captured_fig_shape[0]
                inter_height = figures_per_col*assets.captured_fig_shape[1]

                shape = (
                    int(margins[0] * 2 + inter_width), 
                    int(margins[1] * 2 + inter_height)
                )

                self._orig_shape = shape
                self._orig_inter = (inter_width, inter_height)

                background = assets.make_raw_plaque(shape=shape)

                plaque_tint = phase(background, color=assets.scheme.plaque.new_opacity(plaque_opacity))
                player_tint = phase(background, color=assets.scheme.players[player_index].new_opacity(player_opacity))
                
                background.blit(plaque_tint, (0,0))
                background.blit(player_tint, (0,0))

                self.INIT_X = 0
                self.MAX_X = (figures_per_row-1)*assets.captured_fig_shape[0]

                self.CURRENT_X = self.INIT_X
                self.CURRENT_Y = 0

                super().__init__(background, item=objects.Array((inter_width, inter_height)), margins=margins)

            def clear(self):
                self.item = objects.Array(self._orig_inter)

                self.CURRENT_X = 0
                self.CURRENT_Y = 0


            def add(self, piece : Piece | tuple[str, int]):
                if isinstance(piece, Piece):
                    sprite = assets.colored_capt_figs[piece.player_index][piece.name]
                elif isinstance(piece, tuple):
                    name, index = piece
                    sprite = assets.colored_capt_figs[index][name]
                else:
                    raise TypeError(piece.__class__.__name__)
                
                obj = objects.Object(sprite)

                if self.CURRENT_Y >= self.item.height:
                    self.item._set(new_surface((self.item.width, self.item.height + assets.captured_fig_shape[1])), fixed='topleft')
                    
                obj.topleft = (self.CURRENT_X, self.CURRENT_Y)
                
                self.CURRENT_X += (assets.captured_fig_shape[0])
                        
                if self.CURRENT_X > self.MAX_X:
                    self.CURRENT_X = self.INIT_X
                    self.CURRENT_Y += (assets.captured_fig_shape[1])

                self.item.append(obj)


        class SideBar(FocusContainer[SystemRequest]):
            def __init__(
                self,
                
                env_height : int,

                figures_per_row : int = 6,
                figures_per_col : int = 2,

                arr_margin : float = 4,
                clock_margin : float = 3,

                margin : float = 4,

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

                env_w = max(arr_shape[0] + 2 * self.margins[0], (clock_shape[0] + 2*self.margins[0]))
                env_h = env_height

                assert (env_h >= 2 * (3*self.margins[1] + arr_shape[1] + clock_shape[1]))

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

                self.player_index = player_index

                self.append(self.clocks[0])
                self.append(self.clocks[1])
                self.append(self.arrs[0])
                self.append(self.arrs[1])


            def clear(self):
                for arr in self.arrs:
                    arr.clear()

            def set_times(self, times_s : Sequence[float]):
                for time_s, clock in zip(times_s, self.clocks):
                    clock.set_time(time_s)


            def add(self, player_index : int, piece : Piece | tuple[str, int]):
                self.arrs[player_index].add(piece)

            
            
        class ChatBar(FocusContainer[SystemRequest]):
            def __init__(
                self,
                
                env_height : int,

                chat_dims : Dimensions = (4, 3),
                entry_dims : Dimensions = (4, 1.5),

                margin : float = 8,
                text_margin : float = 5,

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

                font = assets.half_text_font
                
                self.player_index = player_index

                self.text_colors = assets.scheme.chat_texts
                self.outgoing_color = self.text_colors[player_index]

                text_margins = assets.pixels_to_coords(text_margin)

    
                chat_box = TextRecord(font=font, width = chat_shape[0] - 2 * text_margins[0])

                #if chat_history is not None:
                #    for chat, i in chat_history:
                #        chat_box.register(chat, i, color=assets.scheme.chat_texts[i])

                chat_view = Scrollable(chat_plaque, chat_box, margins=text_margins)
                chat_view.topleft = chat_topleft

                entry_view = InputField(font=font, shape=entry_shape, color=self.outgoing_color, margin=text_margin)
                entry_view.topleft = entry_topleft

                self.chat_view = chat_view
                self.entry_view = entry_view

                self.append(chat_view)
                self.append(entry_view)

            def register_text(self, text : Text):
                self.chat_view.item.register(text.content, color=self.text_colors[text.index])
                
            def register_chat(self, chat : list[Text]):
                for text in chat:
                    self.chat_view.item.register(text.content, color=self.text_colors[text.index])

            def show_message(self, message : Error | Response | EngineError | EngineResponse, lifespan : float = 5):
                message_popup = MessagePopup(message.__class__.__name__, message, text_color=assets.scheme.error if isinstance(message, (Error, EngineError)) else assets.scheme.text)

                message_popup.topleft = self.margins 
                self.append_temp(message_popup, lifespan=lifespan)


            def handle(self, event : EventUI, queue : list[SystemRequest]):
                super().handle(event, queue)

                if event.type == pg.KEYDOWN and event.key == pg.K_RETURN and self.focus is self.entry_view:
                    result = Text(
                        index=self.player_index,
                        content=self.entry_view.item.clear()
                    )

                    queue.append(result)
        

        class EnvContainer(FocusContainer[SystemRequest]):

            def _quit(self, queue : list[SystemRequest]):
                queue.append(
                    Request("quit")
                )

            def show_message(self, message : Error | Response | EngineError | EngineResponse, lifespan : float = 5):
                message_popup = MessagePopup(message.__class__.__name__, message, text_color=assets.scheme.error if isinstance(message, (Error, EngineError)) else assets.scheme.text)

                if hasattr(self, 'margins'):
                    message_popup.topleft = self.margins 
                self.append_temp(message_popup, lifespan=lifespan)


        class GameInterface(EnvContainer):
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
                assets.play_sound("start")
                ###
                
                self.chatbar = chatbar
                self.append(chatbar)

                self.statbar = statbar
                self.append(statbar)

                self.player_index = player_index
                
                self.text_colors = assets.scheme.chat_texts

                self.running = True
        

            def _set_board(self, board : Board):
                board.set_player(self.player_index)
                board.enforce_player = self.board.enforce_player
                board.topleft = self.board.topleft 

                self.clear()
                self.append(board)
                self.board = board 
                self.append(self.chatbar)
                self.append(self.statbar)

                assets.play_sound("start")


            def register(self, msg : SystemResponse):
                if isinstance(msg, Layout):
                    self._set_board(deserialize(msg.board_str))
                    self.statbar.clear()
                    #TODO: fix this ^^^ how do we know which player is which
            
                elif isinstance(msg, EngineResponse):
                    self.board.register_response(msg)
                    if msg.label == "times" and self.board.end_plaque is None:
                        self.statbar.set_times(msg.content)
                
                elif isinstance(msg, EngineEvent):
                    result = self.board.register_event(msg)
                    if result is not None:
                        self.statbar.add(*result)

                elif isinstance(msg, EngineError):
                    self.board.register_error(msg)

                elif isinstance(msg, Text):
                    self.chatbar.register_text(msg)

            def show_message(self, message : Error | Response | EngineError | EngineResponse, lifespan : float = 5):
                self.chatbar.show_message(message, lifespan=lifespan)
                


        # NEW THINGS....

        # work on making sign-up/login page, etc...
        class AuthInterface(EnvContainer):
            def __init__(
                self, 
                glyph_length : int, 
                text_margin : float = 3, 
                margin : float = 5,
                fill_color : Color = assets.scheme.plaque
            ):
                
                font = assets.half_text_font

                self.login_button = login_button = Button('LOG IN')
                self.signup_button = signup_button = Button('SIGN UP')

                self.margins = assets.pixels_to_coords(margin)

                entry_width = (font.glyph_width + font.gap_size) * glyph_length
                self.username_entry = username_entry = InputField(font, entry_width, color=assets.scheme.text, margin=text_margin, small_corners=True, background_color=assets.scheme.button, default_text='Enter your username')
                self.password_entry = password_entry = InputField(font, entry_width, color=assets.scheme.text, margin=text_margin, small_corners=True, background_color=assets.scheme.button, default_text='Enter your password')

                buttons_width = login_button.width + signup_button.width + self.margins[0]
                
                env_shape = (max(buttons_width, username_entry.width, online_logo.width) + self.margins[0] * 2, signup_button.height + username_entry.height * 2 + self.margins[1] * 5 + online_logo.height)

                super().__init__(env_shape)
                self.surface.fill(fill_color.rgb)

                online_logo.center = self.center 
                online_logo.top = self.margins[1]

                online_logo.blit_onto(self.surface)

                login_button.bottomleft = (self.margins[0], env_shape[1] - self.margins[1])
                signup_button.bottomright = (env_shape[0] - self.margins[0], env_shape[1] - self.margins[1])

                password_entry.bottomleft = (self.margins[0], login_button.top - self.margins[1])
                username_entry.bottomleft = (self.margins[0], password_entry.top - self.margins[1])

                self.append(username_entry)
                self.append(password_entry)
                self.append(login_button)
                self.append(signup_button)



            def read_to(self, queue : list[SystemRequest], is_new : bool = False) -> bool:
                if self.username_entry.item.string != '' and self.password_entry.item.string != '':
                    queue.append(
                        Auth(
                            username=self.username_entry.item.read(),
                            password=self.password_entry.item.read(),
                            is_new=is_new
                        )
                    )

                    return True
                return False 

            def drain_to(self, queue : list[SystemRequest], is_new : bool = False) -> bool:
                if self.username_entry.item.string != '' and self.password_entry.item.string != '':
                    queue.append(
                        Auth(
                            username=self.username_entry.item.clear(),
                            password=self.password_entry.item.clear(),
                            is_new=is_new
                        )
                    )

                    return True
                return False 
                

            def handle(self, event : EventUI, queue : list[SystemRequest]):
                is_tab = False

                if event.type == pg.KEYDOWN:
                    if event.key == pg.K_TAB:
                        is_tab = True
                        if self.focus is self.username_entry:
                            self.mediate_focus(self.password_entry)
                        elif self.focus is self.password_entry:
                            self.mediate_focus(None)

                    if event.key == pg.K_RETURN:
                        self.read_to(queue)
                        self.mediate_focus(None)
                
                if event.type == pg.MOUSEBUTTONDOWN and event.button <= 2:
                    if self.login_button.hits(event.pos):
                        if self.read_to(queue):
                            self.login_button.click()
                        
                    if self.signup_button.hits(event.pos):
                        if self.read_to(queue, is_new=True):
                            self.signup_button.click()
                    
                if event.type == pg.MOUSEBUTTONUP and event.button <= 2:
                    self.login_button.unclick()
                    self.signup_button.unclick()

                if not is_tab:
                    super().handle(event, queue)


        class PlaySelection(FocusContainer[SystemRequest]):
            def __init__(self, shape : Coords, sets : list[str] = ['Chess', 'Shatranj', 'Wildebeest'], times : list[str] = ['5:00', '10:00', '20:00'], margin : float = 3, background_color : Color | str = assets.scheme.plaque):
                
                self.receiver_name = None 

                width, height = shape

                self.margins = margins = assets.pixels_to_coords(margin)
                bar_width = (width - 3*margins[0]) // 2

                font = assets.half_text_font

                play_button = Button('PLAY', font=font)
                close_button = Button('CLOSE', font=font)

                set_selection_height = height - (2*margins[1])
                time_selection_height = height - (3 * margins[1] + play_button.height)

                set_selection = ScrollableSelection(
                    (bar_width, set_selection_height),
                    choices=sets, font=font
                )

                time_selection = ScrollableSelection(
                    (bar_width, time_selection_height),
                    choices=times, font=font
                )

                self.set_select = set_selection
                self.time_select = time_selection

                self.play_button = play_button
                self.close_button = close_button

                plaque = assets.make_plaque((width, height), small_corners=True, color=background_color)
                super().__init__(plaque)
                
                set_selection.topleft = margins 
                time_selection.topleft = (2*margins[0] + set_selection.width, margins[1])
                close_button.topright = (self.width - margins[0], time_selection.bottom + margins[1])
                play_button.topright = (close_button.left - margins[0], close_button.top)

                self.append(set_selection)
                self.append(time_selection)
                self.append(play_button)
                self.append(close_button)
            
            
            def toggle_keep(self):
                self.set_select.item.toggle_keep()
                self.time_select.item.toggle_keep()

            def defocus(self):
                self.set_select.defocus()
                self.time_select.defocus()

                super().defocus()
            

        class ChallengePopup(objects.Array, Controllable[SystemRequest]):
            def __init__(self, challenge : Challenge, font : Font = assets.half_title_font, text_color : Color = assets.scheme.text, margin : float = 3, figure : str = "Pawn", background_color : Color = assets.scheme.plaque, button_color : Color = assets.scheme.button):
                symbol = objects.Object(assets.figures[figure])

                self.margins = assets.pixels_to_coords(margin)

                minutes = challenge.timer//60
                seconds = int(challenge.timer - int(challenge.timer/60)*60)

                minutes = str(minutes)
                seconds = str(seconds) if seconds >= 10 else f'0{seconds}'
                
                text_surface = objects.Object(font.render(f'{challenge.sender} - {challenge.game_set} - {minutes}:{seconds}', color=text_color))

                self.accept = accept_button = Button('accept', color=text_color, background_color=button_color)
                self.decline = decline_button = Button('decline', color=text_color, background_color=background_color)

                width = 3*self.margins[0] + symbol.width + max(text_surface.width, accept_button.width + decline_button.width + self.margins[0])
                height = 2 * self.margins[1] + max(symbol.height, text_surface.height + int(0.5*self.margins[1]) + accept_button.height)

                plaque = assets.make_plaque((width, height), small_corners=True, color=background_color)

                super().__init__(plaque)

                symbol.center = self.midpoint
                symbol.left = self.margins[0]

                symbol.blit_onto(self.surface)

                text_surface.top = self.margins[1]
                text_surface.left = symbol.right + self.margins[0]

                text_surface.blit_onto(self.surface)

                accept_button.left = text_surface.left 
                decline_button.left = accept_button.right + self.margins[0]

                accept_button.bottom = decline_button.bottom = height - self.margins[1]

                self.append(accept_button)
                self.append(decline_button)
                self.challenge = challenge

            
            def handle(self, event : EventUI, queue : list[SystemRequest]):
                # TODO: fix all mousebuttondown things to generalize nicely with mousebuttonup
                if event.type == pg.MOUSEBUTTONDOWN and event.button <= 2:
                    i = self.which_hits(event.pos)

                    if i == 0:
                        self.accept.click()
                        queue.append(
                            Request('accept', self.challenge.game_id)
                        )
                        self.__container__.resolve_challenge(self)
                        self.__container__.mediate_focus(None)
                    elif i == 1:
                        self.decline.click()
                        queue.append(
                            Request('decline', self.challenge.game_id)
                        )
                        self.__container__.resolve_challenge(self)
                        self.__container__.mediate_focus(None)


        class MessagePopup(objects.Object):
            def __init__(self, title : str, msg : Error | Response | EngineResponse | EngineError, margin : float = 3, font : Font = assets.quarter_text_font, text_color : Color = assets.scheme.error, background_color : Color = assets.scheme.button):

                self.margins = assets.pixels_to_coords(margin)

                label_surface = objects.Object(font.render(f"{title}: {msg.label}", color=text_color))
                content_surface = objects.Object(font.render(msg.content, color=text_color))

                width = max(label_surface.width, content_surface.width) + 2*self.margins[0]
                height = label_surface.height + content_surface.height + int(2.5*self.margins[1])
                
                label_surface.topleft = self.margins
                content_surface.topleft = (self.margins[0], label_surface.bottom + int(0.5*self.margins[1]))
                plaque = assets.make_plaque((width, height), small_corners=True, color=background_color)

                label_surface.blit_onto(plaque)
                content_surface.blit_onto(plaque)

                super().__init__(plaque)


        class MiddleInterface(EnvContainer):
            def __init__(self, username : str, glyphs_per_line : int, tabs_per_view : float = 6.5, font : Font = assets.half_text_font, view_margin : float = 3, margin : float = 5, fill_color : Color = assets.scheme.plaque):
                
                self.margins = assets.pixels_to_coords(margin)
                view_margins = assets.pixels_to_coords(view_margin)

                self.username = username
                username_text = objects.Object(font.render(username))
                

                button_width = int(glyphs_per_line * (font.glyph_width + font.gap_size))
                test_button = Button('test', min_width=button_width, font=font, color=text_color, margin=margin)

                view_shape = ( 
                    button_width + 2*view_margins[0],
                    int(tabs_per_view * test_button.height) + 2*view_margins[1]
                )

                shape = (max(view_shape[0], online_logo.width) + 2*self.margins[0], view_shape[1] + 3*self.margins[1] + online_logo.height)

                super().__init__(shape)
                self.surface.fill(fill_color.rgb)

                online_logo.center = self.center 
                online_logo.top = self.margins[1]

                online_logo.blit_onto(self.surface)

                # CHANGE THIS:
                # instead of scrollable dropdowns, just have a separate window. it is easier.

                self.selection = ScrollableSelection(view_shape, choices=[], font=font, anchor='left', view_margin=view_margin, button_color=assets.scheme.plaque, background_color=assets.scheme.button)
                self.selection.bottomleft = (self.margins[0], self.height - self.margins[1])

                self.proposal = PlaySelection(view_shape)
                self.proposal.bottomleft = self.selection.bottomleft

                self.proposing = False

                self.challenge_popups = []

                username_text.topright = (shape[0] - self.margins[0], self.margins[1])

                self.CURRENT_Y = 0 
                self.append(self.selection)
                self.append(username_text)

            def add(self, user : UserLayout):
                self.selection.add(user.username)
            
            def delete(self, user : UserLayout):
                self.selection.delete(user.username)                
            
            def show_challenge(self, challenge : Challenge):
                challenge_popup = ChallengePopup(challenge)

                if not self.challenge_popups:
                    challenge_popup.topright = (self.width - self.margins[0], self.margins[1])
                else:
                    challenge_popup.topright = (self.width - self.margins[0], self.challenge_popups[-1].bottom + int(0.5*self.margins[1]))

                self.challenge_popups.append(challenge_popup)
                self.append(challenge_popup)
            
            def resolve_challenge(self, cp : ChallengePopup):
                target_index = None
                for i in range(len(self.challenge_popups)):
                    if self.challenge_popups[i] is cp:
                        target_index = i 
                        break

                if target_index is None:
                    return 
                
                self.challenge_popups.remove(cp)
                self.remove(cp)
                shift_ = cp.height + int(0.5*self.margins[1])

                for i in range(target_index, len(self.challenge_popups)):
                    self.challenge_popups[i].top -= shift_

                

            def handle(self, event : EventUI, queue : list[SystemRequest]):
                super().handle(event, queue)

                if self.selection.item.selected is not None and not self.proposing:
                    self.proposing = True
                    self.remove(self.selection)
                    self.append(self.proposal)
                    self.proposal.receiver_name = self.selection.item.selected.string
                    self.proposal.toggle_keep()
                    self.proposal.enfocus()

                if self.proposing and event.type == pg.MOUSEBUTTONDOWN and event.button <= 2: 
                    if self.proposal.close_button.hits(event.pos):
                        self.proposing = False 
                        self.proposal.close_button.click()
                        self.remove(self.proposal)
                        self.append(self.selection)
                        self.selection.defocus()
                        self.proposal.toggle_keep()
                        self.proposal.defocus()
                        self.proposal.play_button.unclick()
                        self.proposal.close_button.unclick()
                    elif self.proposal.play_button.hits(event.pos):
                        if self.proposal.set_select.item.selected is not None and self.proposal.time_select.item.selected is not None:
                            self.proposal.play_button.click()
                            minutes, seconds = self.proposal.time_select.item.selected.string.split(':')
                            queue.append(
                                Challenge(
                                    sender=self.username,
                                    receiver=self.proposal.receiver_name,
                                    game_set=self.proposal.set_select.item.selected.string,
                                    timer=int(minutes)*60+int(seconds)
                                )
                            )
                        
                    

                
                
                            


                


        this.Piece = Piece
        this.Board = Board

        this.Timer = Timer 
        this.FigureArray = FigureArray

        this.SideBar = SideBar
        this.ChatBar = ChatBar

        this.GameInterface = GameInterface
        this.AuthInterface = AuthInterface

        this.MiddleInterface = MiddleInterface
        


UIType = UserInterface | Assets | Coords | tuple[float, float] | Dimensions | int | float

def to_UI(obj : UIType):
    if isinstance(obj, UserInterface):
        return obj
    if isinstance(obj, Assets):
        return UserInterface(assets=obj)
    else:
        return UserInterface(assets=Assets(scaling=obj))