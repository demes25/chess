# Demetre Seturidze
# Chess
# User Interface / Run Loop

from files.game import *
import pygame as pg
from files.boards import Board
from files.resources import load_sprite, new_surface, Surface, tint, FONT_FILE

RAISE = False

class GUI:
    def __init__(
        self,
        board : Board,
        caption : str = 'Chussy',

        title_font_size : float = 0.5, 
        caption_font_size : float = 0.3,
        plaque_opacity : int = 230, # opacity for plaques
        selection_opacity : int = 210 # alpha for selection tiles.
    ):

        self.board = board 

        self.screen = pg.display.set_mode((board.width, board.height))
        pg.display.set_caption(caption)

        self.title_font = pg.font.Font(FONT_FILE, int(board.tile_height * title_font_size))
        self.caption_font = pg.font.Font(FONT_FILE, int(board.tile_height * caption_font_size))

        self.selection_opacity = selection_opacity
        
        self.mouse_dragging = False 

        # wraps a surface to be able to blit/move easier.
        # also makes registering hits easier
        class Object:
            def __init__(obj, surface : Surface):
                obj.surface = surface 
                obj.rect = surface.get_rect()
            
            # blits this object to the screen
            def blit(obj):
                self.screen.blit(obj.surface, obj.rect)

            # returns true if both (or the one given) sets of coordinates collide with this object
            def hits(obj, coords : Tuple[int, int], prev_coords : Tuple[int, int] | None = None):
                if prev_coords is None:
                    return obj.rect.collidepoint(coords)
                else:
                    return obj.rect.collidepoint(coords) and obj.rect.collidepoint(prev_coords)
        
        # creates a plaque
        class Plaque(Object):
            # blocks with which we can construct plaques 
            blocks = {
                's' : load_sprite('tiles/Box', dims=board.tile_dims), # single

                't' : load_sprite('tiles/Top', dims=board.tile_dims), # top
                'b' : load_sprite('tiles/Bottom', dims=board.tile_dims), # bottom
                'v' : load_sprite('tiles/Vertical', dims=board.tile_dims), # vertical

                'l' : load_sprite('tiles/Left', dims=board.tile_dims), # left
                'r' : load_sprite('tiles/Right', dims=board.tile_dims), # right
                'h' : load_sprite('tiles/Horizontal', dims=board.tile_dims), # horizontal


                'le' : load_sprite('tiles/LeftEdge', dims=board.tile_dims), # left edge
                're' : load_sprite('tiles/RightEdge', dims=board.tile_dims), # right edge
                'te' : load_sprite('tiles/TopEdge', dims=board.tile_dims), # top edge
                'be' : load_sprite('tiles/BottomEdge', dims=board.tile_dims), # bottom edge

                'tl' : load_sprite('tiles/TopLeft', dims=board.tile_dims), # top left
                'bl' : load_sprite('tiles/BottomLeft', dims=board.tile_dims), # bottom left
                'tr' : load_sprite('tiles/TopRight', dims=board.tile_dims), # top right
                'br' : load_sprite('tiles/BottomRight', dims=board.tile_dims), # bottom right

                'm' : load_sprite('tiles/Middle', dims=board.tile_dims) # middle
            }

            # constructs a plaque using blocks sprites
            # width and height are the dimensions of the plaque in terms of tiles, 
            # i.e. 3x5 would return a 3 tile by 5 tile plaque
            def __init__(plq, dims : Tuple[int, int]):
                tile_w = board.tile_width
                tile_h = board.tile_height
                color = board.scheme['plaque']
                opacity = plaque_opacity
                width, height = dims 

                # special cases if any of the dimensions are one
                if width == 1 and height == 1:
                    plq.surface = tint(Plaque.blocks['s'].copy(), color=color, opacity=opacity)
                
                elif width == 1:
                    surface = new_surface((tile_w, height * tile_h))

                    t = Plaque.blocks['t']
                    b = Plaque.blocks['b']
                    v = Plaque.blocks['v']

                    surface.blit(t, (0, 0))
                    surface.blit(b, (0, (height-1)*tile_h))

                    for i in range(1, height-1):
                        surface.blit(v, (0, i*tile_h))
                    
                    plq.surface = tint(surface, color=color, opacity = opacity)

                elif height == 1:
                    surface = new_surface((width * tile_w, tile_h))

                    l = Plaque.blocks['l']
                    r = Plaque.blocks['r']
                    h = Plaque.blocks['h']

                    surface.blit(l, (0, 0))
                    surface.blit(r, ((width-1)*tile_w, 0))

                    for i in range(1, width-1):
                        surface.blit(h, (i*tile_w, 0))
                    
                    plq.surface = tint(surface, color=color, opacity = opacity)

                else:
                    surface = new_surface((width * tile_w, height * tile_h))

                    tl = Plaque.blocks['tl']
                    bl = Plaque.blocks['bl']
                    tr = Plaque.blocks['tr']
                    br = Plaque.blocks['br']

                    BOTTOM = (height-1) * tile_h 
                    RIGHT = (width-1) * tile_w 

                    surface.blit(tl, (0, 0))
                    surface.blit(bl, (0, BOTTOM))
                    surface.blit(tr, (RIGHT, 0))
                    surface.blit(br, (RIGHT, BOTTOM))

                    te = Plaque.blocks['te']
                    be = Plaque.blocks['be']
                    le = Plaque.blocks['le']
                    re = Plaque.blocks['re']
                    
                    for i in range(1, width-1):
                        I = i * tile_w 
                        surface.blit(te, (I, 0))
                        surface.blit(be, (I, BOTTOM))
                    
                    for i in range(1, height-1):
                        I = i * tile_h 
                        surface.blit(le, (0, I))
                        surface.blit(re, (RIGHT, I))
                    
                    m = Plaque.blocks['m']
                    for i in range(1, width-1):
                        for j in range(1, height-1):
                            surface.blit(m, (i * tile_w, j * tile_h))
                    
                    plq.surface = tint(surface, color=color, opacity=opacity)

                plq.rect = plq.surface.get_rect()
            
            def blit(plq):
                self.screen.blit(plq.surface, plq.rect)


        # a promotion plaque, depending on the choice of 
        # figures, and the position on the screen 
        class PromotionPlaque(Plaque):
            def __init__(plq, figures : List[Figure], board_pos : Tuple[int, int]):
                plq.figures = figures
                plq.objects = [Object(figure.sprite) for figure in figures]

                # rudimentary: for now, the default is that the promotion plaque 
                # extends rightwards from the promotion square, unless that clashes with 
                # board dimensions, in which case we go leftwards.
                # TODO: extend this to be able to be a square or some other dimension to accommodate n promotion figures
                if (board.dimensions[0]-board_pos[0]) < len(figures):
                    disp = -board.tile_width
                else:
                    disp = board.tile_width
                
                x, y = board.coords(board_pos)
                fx = x
                for obj in plq.objects:
                    obj.rect.center = (fx, y)
                    fx += disp

                plq.width = width = len(figures)
                super().__init__((width, 1))

                # set the center of the plaque
                plq.rect.center = (x + int(disp*(width -1)/2.0), y)
            
            def blit(plq):
                super().blit()
                for obj in plq.objects:
                    obj.blit()

            # returns the figure which the given coordinates collide with
            def which_hits(plq, coords : Tuple[int, int], prev_coords : Tuple[int, int] | None = None) -> Figure:
                for i in range(plq.width):
                    if plq.objects[i].hits(coords, prev_coords):
                        return plq.figures[i]
                
                return None 


        self.Object = Object
        self.Plaque = Plaque 
        self.PromotionPlaque = PromotionPlaque

        self._construct_game_over_plaque()
        self.promotion : PromotionPlaque | None = None



    # constructs the game over plaque and necessary objects
    def _construct_game_over_plaque(self):
        plaque = self.Plaque((5, 3))
        x, y = plaque.rect.center = self.board.center 
        rect = plaque.rect

        checkmate = self.Object(self.title_font.render('Checkmate', True, self.board.scheme['checkmate']))

        stalemate = self.Object(self.title_font.render('Stalemate', True, self.board.scheme['stalemate']))

        dx_r = rect.width // 5
        dx_q = rect.width // 4
        dy = rect.height // 7

        checkmate.rect.center = stalemate.rect.center = (x, y - dy)

        reset_button = self.Object(self.caption_font.render('Reset', True, self.board.scheme['text']))
        reset_button.rect.center = (x - dx_r, y + dy)


        close_button = self.Object(self.caption_font.render('Quit', True, self.board.scheme['text']))
        close_button.rect.center = (x + dx_q, y + dy)

        
        self.game_over_plaque = plaque
        self.checkmate_text = checkmate
        self.stalemate_text = stalemate
        self.reset_button = reset_button
        self.close_button = close_button

    # blits the game over screen (if game over)
    def status_screen(self, status : int):
        if status == Status.ONGOING:
            return 
        elif status == Status.PROMOTING:
            if self.promotion is None:
                piece = self.board.game.promoting
                self.promotion = self.PromotionPlaque(piece.promotion_list, piece.position)
            self.promotion.blit()
        else:
            self.game_over_plaque.blit()
            if status == Status.CHECKMATE:
                self.checkmate_text.blit()
            else:
                self.stalemate_text.blit()

            self.reset_button.blit()
            self.close_button.blit()
    

    def _ingame_event_loop(self, vars : dict) -> List[str]:
        events = []

        for event in pg.event.get():
            if event.type == pg.QUIT:
                vars['running'] = False
            
            if event.type == pg.MOUSEBUTTONDOWN:
                # selects the piece
                self.board.select(event.pos)
            
            if event.type == pg.MOUSEBUTTONUP:
                selected = self.board.selected_piece
                if selected is not None:
                    target = self.board.board_pos(event.pos)

                    if target != selected.position:
                        try:
                            events = self.board.game.move(selected, target)
                        except Exception as e:
                            if not RAISE:
                                self.board.sounds['illegal'].play()
                                print(e)
                            else:
                                raise 
                            
                    
                    self.board.deselect()
        
        return events 
            
    def _game_over_event_loop(self, vars : dict) -> List[str]:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                vars['running'] = False
            
            if event.type == pg.MOUSEBUTTONDOWN:
                vars['click_pos'] = event.pos
            
            if event.type == pg.MOUSEBUTTONUP and vars['click_pos'] is not None:
                if self.reset_button.hits(event.pos, vars['click_pos']): 
                    sound = self.board.begin()
                    sound.play()
                elif self.close_button.hits(event.pos, vars['click_pos']):
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

    def fetch_events(self, vars : dict) -> List[str]:
        status = self.board.game.status 
        if status == Status.ONGOING:
            events = self._ingame_event_loop(vars)
        elif status == Status.PROMOTING:
            events = self._promotion_event_loop(vars)
        else:
            events = self._game_over_event_loop(vars)

        return events 

    # flips a frame given the variables and events
    def frame(self, events : List[str]):
        image, sounds = self.board.update(events, pg.mouse.get_pos())

        self.screen.blit(image, (0,0))
        for sound in sounds:
            sound.play()
        
        # blits a game over screen if the game over value is 1 or 2 (checkmate or stalemate)
        self.status_screen(self.board.game.status)
        pg.display.flip()
            

    def run(self):
        # keeps track of loop parameters to be able to modularize the event loop.
        # this thing gets passed around and edited in-place as opposed to holding
        # all variables locally inside the run function
        vars = {
            'running' : True,
            'click_pos' : None
        }

        start_sound = self.board.begin()
        start_sound.play()

        while vars['running']:
            events = self.fetch_events(vars=vars)
            self.frame(events=events)

            




