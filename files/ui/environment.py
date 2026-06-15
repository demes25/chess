# Demetre Seturidze
# Chess
# Instance

import pygame as pg, time
from typing import Type, Tuple, Callable
from dataclasses import dataclass

from files.logic.game import Game, Status, Event
from netlib.serialization import serialize, deserialize
from files.logic.sets import Set

from files.ui.av import AVType, to_AV, new_window

RAISE = False

# variable settings for the game backend 
@dataclass
class VarSettings:
    running = True 
    click_pos = None 

class GameWindow:
    def __init__(
        self,
        
        set : Type[Set],
        av : AVType,

        # TODO: GENERALIZE FOR SIDEBAR SIZES

        player_index : int =0,
        enforce_player : bool = False,

        topleft : Tuple[int, int] = (0, 0)
    ):
        
        self.game : Game | None = None 
        self.set = set 

        self.av = av = to_AV(av)

        self.board = av.GameBoard(dimensions=set.dimensions, num_players=2, player_index=player_index, topleft=topleft)
        self.sidebar = av.GameSideBar(player_index=player_index, env_height=set.dimensions[1], topleft=self.board.rect.topright)

        self.pixel_width = self.board.pixel_width + self.sidebar.pixel_width
        self.pixel_height = self.board.pixel_height
        
        self.times = None
        self.timeout = False 

        self.player_index = player_index
        self.enforce_player = enforce_player 

        self.var_settings = VarSettings()

        self.topleft = topleft 

        self.game_over_plaque = None
        self.promotion_plaque = None 
        
    # blits the game over screen (if game over)
    def status_screen(self, status : int):
        if status == Status.UNBEGUN or status == Status.ONGOING:
            return 
        elif status == Status.PROMOTING:
            if self.promotion_plaque is None:
                piece = self.game.promoting
                self.promotion_plaque = self.board.make_promotion_plaque(piece.promotion_list, piece.player.index, piece.position)
            self.promotion_plaque.blit_onto(self.board)
        else:
            if self.game_over_plaque is None:
                self.game_over_plaque = self.board.checkmate_plaque if status == Status.CHECKMATE else self.board.stalemate_plaque if status == Status.STALEMATE else self.board.timeout_plaque
            self.game_over_plaque.blit_onto(self.board)



    # checks if the pygame event is global and executes
    # this is defined because it will be used across all event loops
    def _handle_global(self, event : pg.event.Event) -> Event | None:
        result = None 
        if event.type == pg.QUIT:
            result = self._quit()
        
        
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
            
    def _handle_gameover(self, event : pg.event.Event) -> Event:
        result = Event()
            
        if event.type == pg.MOUSEBUTTONDOWN:
            self.var_settings.click_pos = event.pos
        
        if event.type == pg.MOUSEBUTTONUP and self.var_settings.click_pos is not None:
            reset = self.game_over_plaque.objects[0]
            quit = self.game_over_plaque.objects[1]

            if reset.hits(event.pos, self.var_settings.click_pos): 
                result = Event(label='reset')
            elif quit.hits(event.pos, self.var_settings.click_pos):
                result = self._quit()
        
        return result
    
    def _handle_promotion(self, event : pg.event.Event) -> Event:
        result = None

        if event.type == pg.MOUSEBUTTONDOWN:
            self.var_settings.click_pos = event.pos
        
        if event.type == pg.MOUSEBUTTONUP and self.var_settings.click_pos is not None:
            promotion_index = self.promotion_plaque.hit_index(event.pos, self.var_settings.click_pos)
            if promotion_index >= 0:
                if not self.enforce_player or self.game.promoting.player.index == self.player_index:
                    result = self.game.promote(promotion_index=promotion_index)
                    self.promotion_plaque = None
        
        return result
    
    
    # runs an event loop with a given handler.
    # these are defined above for ingame, game_over, and promotion environments
    def event_loop(self, handle : Callable[[pg.event.Event], Event]) -> Event:
        result = Event()

        for event in pg.event.get():
            handle_result = self._handle_global(event)
            if handle_result is None:
                handle_result = handle(event)
            if handle_result is not None:
                result = handle_result 

        return result 
    
    def update_times(self):
        if self.game.status == Status.ONGOING:
            turn_start_clock = self.game.times[self.game.turn]
            self.times[self.game.turn] = turn_start_clock - (time.time() - self.game.turn_start_time)

            if any(i <= 0 for i in self.times):
                self.game.status = Status.TIMEOUT

        
    def clear(self):
        self.board.selected_piece = None 
        self.promotion_plaque = None 
        self.game_over_plaque = None 
        self.timeout = False 

        self.var_settings = VarSettings()
        self.board.deselect_squares()

    def begin(self, game = None, timer = 600):
        self.clear()
        self.game = game if game is not None else self.set(timer)
        self.times = self.game.times.copy()

    def _quit(self) -> Event:
        self.var_settings.running = False 
        return Event('quit')

    def fetch_event(self) -> Event:
        status = self.game.status 
        if status == Status.UNBEGUN or status == Status.ONGOING:
            handle = self._handle_ingame
        elif status == Status.PROMOTING:
            handle = self._handle_promotion
        else:
            handle = self._handle_gameover
        
        return self.event_loop(handle=handle) 

    # updates the audio-visual state:
    # draws the current surface and plays all sounds in the given event.
    def update_state(self, event : Event):
        self.update_times()
        self.board.draw(self.game.pieces, pg.mouse.get_pos())
        self.sidebar.draw(self.times, self.game.captured_pieces)

        if self.game.status == Status.TIMEOUT and not self.timeout:
            event.label = 'timeout'
            self.board.play('end')
            self.timeout = True 
        else:
            for sound in event.sounds:
                self.board.play(sound)
        
        # blits a game over screen if the game over value is 1 or 2 (checkmate or stalemate)
        self.status_screen(self.game.status)

    # fetches the current event, updates the audiovisual state, and blits onto the given screen
    # returns the fetched event
    def frame(self, screen : pg.Surface) -> Event:
        event = self.fetch_event()
        self.update_state(event=event)
        self.board.blit_onto(screen)
        self.sidebar.blit_onto(screen)
        return event

    # registers received events (as opposed to producing events)
    def register(self, event : Event) -> Event:
        if event.label == 'reset':
            self.begin()
            self.board.play('start')
        if event.label == 'timeout':
            self.game.status = Status.TIMEOUT
            self.board.play('end')

        elif event.label == 'quit':
            self.var_settings.running = False 
        elif event.label == 'action':
            self.game.register_action(event.action)
        
        return event
        

    def run_solo(self, timer = 600, load = 'null'):
        # keeps track of loop parameters to be able to modularize the event loop.
        # this thing gets passed around and edited in-place as opposed to holding
        # all variables locally inside the run function
        self.begin(deserialize(load), timer)
        self.board.play('start')
    
        icon = self.av.assets.colored_figures[0]['King']
        caption = 'OBCHESSED'

        screen = new_window((self.pixel_width, self.pixel_height), icon=icon, caption=caption)

        while self.var_settings.running:
            event = self.frame(screen)
            if event.label == 'reset':
                self.begin(timer=timer)
                self.board.play('start')
            pg.display.flip()

        #debug_serialize(self.game)
        
        with open('game.txt', 'w') as f:
            f.write(serialize(self.game, indent = 2))
        

        
