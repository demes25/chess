# Demetre Seturidze
# Chess
# Client

from files.logic.game import *
import pygame as pg
from files.logic.sets import Set
from files.media.assets import AudioVisuals, Assets, new_surface
from dataclasses import dataclass

RAISE = False 

# variable settings for the game backend 
@dataclass
class VarSettings:
    running = True 
    click_pos = None 

class GameInstance:
    def __init__(
        self,
        
        set : Type[Set],
        assets : Assets
    ):
        self.set = set
        self.game : Game | None = None 
        self.assets = assets
        self.av = AudioVisuals(assets, dimensions=set.dimensions, num_players=2, player_index=1)

        self.var_settings = VarSettings()

        self.surface = new_surface((self.av.width, self.av.height))

        self.game_over_plaque = None
        self.promotion_plaque = None 

    # blits the game over screen (if game over)
    def status_screen(self, status : int):
        if status == Status.ONGOING:
            return 
        elif status == Status.PROMOTING:
            if self.promotion_plaque is None:
                piece = self.game.promoting
                self.promotion_plaque = self.av.make_promotion_plaque(piece.promotion_list, piece.player.index, piece.position)
            self.promotion_plaque.blit_onto(self.surface)
        else:
            if self.game_over_plaque is None:
                self.game_over_plaque = self.av.checkmate_plaque if status == Status.CHECKMATE else self.av.stalemate_plaque
            self.game_over_plaque.blit_onto(self.surface)
    

    # for all of these: vars contains
    def _ingame_event_loop(self) -> Event:
        result = Event()

        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.var_settings.running = False
            
            if event.type == pg.MOUSEBUTTONDOWN:
                # selects the piece
                pos = self.av.board_pos(event.pos)
                target = self.game.at(pos)
                selected = self.av.selected_piece

                if selected is None or (target is not None and target.player == selected.player):
                    self.av.deselect_squares()
                    self.av.select_piece(target)
                elif target != selected:
                    try:
                        result = self.game.move(selected, pos)
                        self.av.select_square(pos)
                    except Exception as e:
                        self.av.deselect_squares()
                        
                    self.av.deselect_piece()
            
            if event.type == pg.MOUSEBUTTONUP:
                selected = self.av.selected_piece

                if selected is not None:
                    pos = self.av.board_pos(event.pos)
                    if pos != selected.position:
                        try:
                            result = self.game.move(selected, pos)
                            self.av.select_square(pos)
                        except Exception as e:
                            if not RAISE:
                                self.av.play('illegal')
                                print(e)
                                self.av.deselect_squares()
                            else:
                                raise 
                        
                        self.av.deselect_piece()
                    
                    else:
                        self.av.hold_selected = False 
        
        return result 
            
    def _game_over_event_loop(self) -> Event:
        result = Event()

        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.var_settings.running = False
            
            if event.type == pg.MOUSEBUTTONDOWN:
                self.var_settings.click_pos = event.pos
            
            if event.type == pg.MOUSEBUTTONUP and self.var_settings.click_pos is not None:
                reset = self.game_over_plaque.objects[0]
                quit = self.game_over_plaque.objects[1]

                if reset.hits(event.pos, self.var_settings.click_pos): 
                    result = Event(label='reset')
                    self.begin()
                elif quit.hits(event.pos, self.var_settings.click_pos):
                    result = Event(label='quit')
                    self.var_settings.running = False
        
        return result
    
    def _promotion_event_loop(self) -> List[str]:
        result = Event()

        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.var_settings.running = False
            
            if event.type == pg.MOUSEBUTTONDOWN:
                self.var_settings.click_pos = event.pos
            
            if event.type == pg.MOUSEBUTTONUP and self.var_settings.click_pos is not None:
                promotion_index = self.promotion_plaque.hit_index(event.pos, self.var_settings.click_pos)
                if promotion_index >= 0:
                    result = self.game.promote(promotion_index=promotion_index)
                    self.promotion_plaque = None
                    # if the player is out of legal moves, the game ends
        
        return result

    def begin(self):
        self.game = self.set.new_game()

        self.av.selected_piece = None 
        self.promotion_plaque = None 
        self.game_over_plaque = None 

        self.var_settings = VarSettings()
        self.av.deselect_squares()
        
        self.av.play('start')

    def fetch_event(self) -> Event:
        status = self.game.status 
        if status == Status.ONGOING:
            event = self._ingame_event_loop()
        elif status == Status.PROMOTING:
            event = self._promotion_event_loop()
        else:
            event = self._game_over_event_loop()

        return event 

    # flips a frame given the variables and events
    def frame(self, event : Event):
        self.av.draw(self.surface, self.game.pieces, pg.mouse.get_pos())

        for sound in event.sounds:
            self.av.play(sound)
        
        # blits a game over screen if the game over value is 1 or 2 (checkmate or stalemate)
        self.status_screen(self.game.status)

    # registers received events (as opposed to producing events)
    def register(self, event : Event) -> Event:
        if event.label == 'none':
            return event 
        elif event.label == 'reset':
            self.begin()
            return event
        elif event.label == 'quit':
            self.var_settings.running = False 
            return event
        elif event.label == 'move':
            s, e = event.displacement
            re_event = self.game.move(self.game.at(s), e)

            if event.promote_to > 0:
                event.sounds.append('promote')
                self.game.promote(event.promote_to)
            return re_event 
        elif event.label == 'promote':
            return self.game.promote(event.promote_to)
        

    def run_solo(self):
        # keeps track of loop parameters to be able to modularize the event loop.
        # this thing gets passed around and edited in-place as opposed to holding
        # all variables locally inside the run function
        self.begin()
        pg.display.init()
        screen = pg.display.set_mode((self.av.width, self.av.height))

        while self.var_settings.running:
            event = self.fetch_event()
            self.frame(event=event)
            screen.blit(self.surface, (0, 0))
            pg.display.flip()





