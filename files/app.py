# Demetre Seturidze
# Chess
# User Interface / Run Loop

from files.logic.game import *
import pygame as pg
from files.logic.sets import Set
from files.media.assets import AudioVisuals, Assets
from files.media.schemes import Scheme, DefaultScheme

RAISE = True

class App:
    def __init__(
        self,
        
        set : Type[Set],
        assets : Assets,

        caption : str = 'Chussy'
    ):
        self.set = set
        self.game : Game | None = None 
        self.assets = assets
        self.av = AudioVisuals(assets, dimensions=set.dimensions, num_players=2)

        self.screen = pg.display.set_mode((self.av.width, self.av.height))
        pg.display.set_caption(caption)

        self.game_over_plaque = None
        self.promotion_plaque = None 

        self.mouse_dragging = False 

    # blits the game over screen (if game over)
    def status_screen(self, status : int):
        if status == Status.ONGOING:
            return 
        elif status == Status.PROMOTING:
            if self.promotion_plaque is None:
                piece = self.game.promoting
                self.promotion_plaque = self.av.make_promotion_plaque(piece.promotion_list, piece.position)
            self.promotion_plaque.blit_onto(self.screen)
        else:
            if self.game_over_plaque is None:
                self.game_over_plaque = self.av.checkmate_plaque if status == Status.CHECKMATE else self.av.stalemate_plaque
            self.game_over_plaque.blit_onto(self.screen)
    

    def _ingame_event_loop(self, vars : dict) -> List[str]:
        events = []

        for event in pg.event.get():
            if event.type == pg.QUIT:
                vars['running'] = False
            
            if event.type == pg.MOUSEBUTTONDOWN:
                # selects the piece
                self.av.selected_piece = self.game.at(self.av.board_pos(event.pos))
            
            if event.type == pg.MOUSEBUTTONUP:
                selected = self.av.selected_piece
                if selected is not None:
                    target = self.av.board_pos(event.pos)

                    if target != selected.position:
                        try:
                            events = self.game.move(selected, target)
                        except Exception as e:
                            if not RAISE:
                                self.av.play('illegal')
                                print(e)
                            else:
                                raise 
                            
                    
                    self.av.selected_piece = None
        
        return events 
            
    def _game_over_event_loop(self, vars : dict) -> List[str]:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                vars['running'] = False
            
            if event.type == pg.MOUSEBUTTONDOWN:
                vars['click_pos'] = event.pos
            
            if event.type == pg.MOUSEBUTTONUP and vars['click_pos'] is not None:
                reset = self.game_over_plaque.objects[0]
                close = self.game_over_plaque.objects[1]

                if reset.hits(event.pos, vars['click_pos']): 
                    self.begin()
                elif close.hits(event.pos, vars['click_pos']):
                    vars['running'] = False
        
        return []
    
    def _promotion_event_loop(self, vars : dict) -> List[str]:
        events = []

        for event in pg.event.get():
            if event.type == pg.QUIT:
                vars['running'] = False
            
            if event.type == pg.MOUSEBUTTONDOWN:
                vars['click_pos'] = event.pos
            
            if event.type == pg.MOUSEBUTTONUP and vars['click_pos'] is not None:
                figure = self.promotion.which_hits(event.pos, vars['click_pos'])
                if figure is not None:
                    events = self.board.game.promote(figure)
                    self.promotion = None
                    # if the player is out of legal moves, the game ends
        
        return events

    def begin(self):
        self.game = self.set.new_game()

        self.av.selected_piece = None 
        self.promotion_plaque = None 
        self.game_over_plaque = None 
        
        self.av.play('start')

    def fetch_events(self, vars : dict) -> List[str]:
        status = self.game.status 
        if status == Status.ONGOING:
            events = self._ingame_event_loop(vars)
        elif status == Status.PROMOTING:
            events = self._promotion_event_loop(vars)
        else:
            events = self._game_over_event_loop(vars)

        return events 

    # flips a frame given the variables and events
    def frame(self, events : List[str]):
        self.av.draw(self.screen, self.game.pieces, pg.mouse.get_pos())

        for event in events:
            self.av.play(event)
        
        # blits a game over screen if the game over value is 1 or 2 (checkmate or stalemate)
        self.status_screen(self.game.status)
        pg.display.flip()
            

    def run(self):
        # keeps track of loop parameters to be able to modularize the event loop.
        # this thing gets passed around and edited in-place as opposed to holding
        # all variables locally inside the run function
        vars = {
            'running' : True,
            'click_pos' : None
        }

        self.begin()

        while vars['running']:
            events = self.fetch_events(vars=vars)
            self.frame(events=events)

            




