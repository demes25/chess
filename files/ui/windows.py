# Demetre Seturidze
# Chess
# Instance

import pygame as pg, time
from typing import Tuple, Callable
from dataclasses import dataclass

from netlib.serialization import serialize, deserialize, Message

from applib.utils import Coords, Vector, ZERO_VEC
from applib.objects import Environment

from files.logic.game import Game, Status, Event
from files.logic.sets import GameSet
from files.ui.av import AVType, to_AV, new_window

RAISE = False

# variable settings for the game backend 
@dataclass
class VarSettings:
    running = True 
    click_pos = None 

class GameWindow(Environment):
    def __init__(
        self,
        
        game_set : GameSet,
        av : AVType,

        # TODO: GENERALIZE FOR SIDEBAR SIZES

        player_index : int =0,
        enforce_player : bool = False,

        default_time_s : float = 600,

        origin : Vector = ZERO_VEC
    ):
        
        self.game : Game | None = None 
        self.game_set = game_set 

        self.av = av = to_AV(av)

        board = av.GameBoard(dims=game_set.dimensions, num_players=2, player_index=player_index)
        chatbar = av.ChatSideBar(env_height = board.shape[1], player_index=player_index)
        statbar = av.GameSideBar(env_height = board.shape[1], player_index=player_index)

        board.topleft = chatbar.topright
        statbar.topleft = board.topright

        shape = (
            chatbar.shape[0] + board.shape[0] + statbar.shape[0],
            board.shape[1]
        )

        super().__init__(shape, origin=origin)

        self.board = self['board'] = board
        self.chatbar = self['chatbar'] = chatbar
        self.statbar = self['statbar'] = statbar

        self.times = None
        self.timeout = False 

        self.player_index = player_index
        self.enforce_player = enforce_player 
        
        self.outgoing_text_color = av.assets.scheme.chat_texts[player_index]
        self.incoming_text_color = av.assets.scheme.chat_texts[(player_index + 1) % 2]

        self.default_time_s = default_time_s

        self.var_settings = VarSettings()

        self.game_over_plaque = None
        self.promotion_plaque = None 

        self.text_mode = False
    

    def enter_text_mode(self):
        if not self.text_mode:
            self.text_mode = True 
            self.chatbar.entry_box.show_pointer()

    def exit_text_mode(self):
        if self.text_mode:
            self.text_mode = False 
            self.chatbar.entry_box.hide_pointer()


    # checks if the pygame event is global and executes
    # this is defined because it will be used across all event loops
    def _handle_global(self, event : pg.event.Event) -> Event | None:
        result = None 
        if event.type == pg.QUIT:
            result = self._quit()
        
        if event.type == pg.MOUSEBUTTONDOWN:
            if self.chatbar.hits(event.pos):
                self.enter_text_mode()
            else:
                self.exit_text_mode()

        return result
        

    def _handle_ingame(self, event : pg.event.Event) -> Event | None:
        result = None 

        if event.type == pg.MOUSEBUTTONDOWN:
            # selects the piece
            pos = self.board.board_pos(event.pos)
            target = self.game.at(pos)
            selected = self.board.selected_piece

            overall_condition = target is None or not self.enforce_player or (target.player.index == self.player_index)

            if overall_condition:
                if selected is None or (target is not None and target.player == selected.player):
                    self.board.deselect_squares()
                    self.board.select_piece(target)
                elif target != selected:
                    try:
                        result = self.game.move(selected, pos)
                        self.board.select_square(pos)
                    except Exception as e:
                        self.board.deselect_squares()
                        
                    self.board.deselect_piece()
        
        if event.type == pg.MOUSEBUTTONUP:
            selected = self.board.selected_piece

            if selected is not None:
                pos = self.board.board_pos(event.pos)
                if pos != selected.position:
                    try:
                        result = self.game.move(selected, pos)
                        self.board.select_square(pos)
                    except Exception as e:
                        if not RAISE:
                            self.board.play('illegal')
                            print(e)
                            self.board.deselect_squares()
                        else:
                            raise 
                    
                    self.board.deselect_piece()
                
                else:
                    self.board.hold_selected = False 
        
        return result
            
    def _handle_gameover(self, event : pg.event.Event) -> Event | None:
        result = None
            
        if event.type == pg.MOUSEBUTTONDOWN:
            self.var_settings.click_pos = event.pos
        
        if event.type == pg.MOUSEBUTTONUP and self.var_settings.click_pos is not None:
            button = self.game_over_plaque.which_hits(event.pos, self.var_settings.click_pos)

            if button == 'reset': 
                result = Event(label='reset')
                self.game_over_plaque = None 

            elif button == 'quit':
                result = self._quit()
        
        return result
    
    def _handle_promotion(self, event : pg.event.Event) -> Event | None:
        result = None

        if event.type == pg.MOUSEBUTTONDOWN:
            self.var_settings.click_pos = event.pos
        
        if event.type == pg.MOUSEBUTTONUP and self.var_settings.click_pos is not None:
            promotion_index = self.promotion_plaque.which_hits(event.pos, self.var_settings.click_pos)

            if promotion_index >= 0:
                if not self.enforce_player or self.game.promoting.player.index == self.player_index:
                    result = self.game.promote(promotion_index=promotion_index)
                    self.promotion_plaque = None
        
        return result
    

    def _handle_text(self, event : pg.event.Event) -> Event | None:
        result = None 

        if event.type == pg.TEXTINPUT:
            text = event.text
            self.chatbar.entry_box.register(text)
        
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_BACKSPACE:
                self.chatbar.entry_box.backspace()
            
            if event.key == pg.K_RETURN:
                text = self.chatbar.entry_box.clear()

                if text != '':
                    result = Event(
                        label='text',
                        text=text
                    )

                    self.chatbar.chat_box.register(text, color=self.outgoing_text_color)

            if event.key == pg.K_LEFT:
                self.chatbar.entry_box.move_ptr_left()
            
            if event.key == pg.K_RIGHT:
                self.chatbar.entry_box.move_ptr_right()
        
    
        return result


        


    # handles the event.
    # subhandlers are defined above for text, ingame, game_over, and promotion environments    
    def handle(self, event : pg.event.Event) -> Event:
        result = self._handle_global(event)

        if result is None:
            if self.text_mode:
                handle = self._handle_text
            else:
                status = self.game.status 
                if status == Status.UNBEGUN or status == Status.ONGOING:
                    handle = self._handle_ingame
                elif status == Status.PROMOTING:
                    handle = self._handle_promotion
                else:
                    handle = self._handle_gameover
    
            result = handle(event)
        
        return result 


    def fetch_event(self) -> Event:
        result = Event()

        for event in pg.event.get():
            handle_result = self.handle(event)
            if handle_result is not None:
                result = handle_result
        
        return result 
    


    def update_times(self):
        if self.game.status == Status.ONGOING:
            turn_start_clock = self.game.times[self.game.turn]
            self.times[self.game.turn] = turn_start_clock - (time.time() - self.game.turn_start_time)

            if any(i <= 0 for i in self.times):
                self.game.status = Status.TIMEOUT

    def blit_onto(self, dest):
        super().blit_onto(dest)

        status = self.game.status

        if status == Status.UNBEGUN or status == Status.ONGOING:
            return 
        elif status == Status.PROMOTING:
            if self.promotion_plaque is None:
                piece = self.game.promoting
                self.promotion_plaque = self.board.make_promotion_plaque(piece.promotion_list, piece.player.index, piece.position)
            self.promotion_plaque.blit_onto(dest)
        else:
            if self.game_over_plaque is None:
                label = 'checkmate' if status == Status.CHECKMATE else 'stalemate' if status == Status.STALEMATE else 'timeout'
                self.game_over_plaque = self.av.GameOverPlaque(label=label)
                self.game_over_plaque.center = self.board.center
            self.game_over_plaque.blit_onto(dest)

        
    def clear(self):
        self.board.selected_piece = None 
        self.promotion_plaque = None 
        self.game_over_plaque = None 
        self.timeout = False 

        self.var_settings = VarSettings()
        self.board.deselect_squares()

    def begin(self, game = None):
        self.clear()
        self.game = game if game is not None else self.game_set.new_game(timer=self.default_time_s)
        self.times = self.game.times.copy()

    def _quit(self) -> Event:
        self.var_settings.running = False 
        return Event('quit')

    # fetches the current event, updates the audiovisual state, and blits onto the given screen
    # returns the fetched event
    def frame(self, screen : pg.Surface) -> Event:
        event = self.fetch_event()

        self.update_times()
        self.board.draw(self.game.pieces)
        self.statbar.draw(self.times, self.game.captured_pieces)

        if self.game.status == Status.TIMEOUT and not self.timeout:
            event.label = 'timeout'
            self.board.play('end')
            self.timeout = True 
        else:
            for sound in event.sounds:
                self.board.play(sound)

        self.blit_onto(screen)

        if self.board.selected_piece is not None and self.board.hold_selected:
            self.board.selected_sprite.center = pg.mouse.get_pos()
            self.board.selected_sprite.blit_onto(screen)

        return event

    # registers received events (as opposed to producing events)
    def register(self, event : Event) -> Event:
        if event.label == 'reset':
            self.begin()
            self.board.play('start')
        elif event.label == 'timeout':
            self.game.status = Status.TIMEOUT
            self.board.play('end')

        elif event.label == 'quit':
            self.var_settings.running = False 
        elif event.label == 'action':
            self.game.register_action(event.action)
            self.times = event.action.times.copy()
        
        elif event.label == 'text':
            self.chatbar.chat_box.register(event.text, color=self.incoming_text_color)
        
        return event
        

    def run_solo(self, load = 'null'):
        # keeps track of loop parameters to be able to modularize the event loop.
        # this thing gets passed around and edited in-place as opposed to holding
        # all variables locally inside the run function
        self.begin(deserialize(load))
        self.board.play('start')
    
        icon = self.av.assets.colored_figures[0]['King']
        caption = 'OBCHESSED'

        screen = new_window(self.shape, icon=icon, caption=caption)

        while self.var_settings.running:
            event = self.frame(screen)
            if event.label == 'reset':
                self.begin()
                self.board.play('start')
            pg.display.flip()

        #debug_serialize(self.game)
        
        with open('game.txt', 'w') as f:
            f.write(serialize(self.game, indent = 2))
        

        
