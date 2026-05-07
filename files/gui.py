# Demetre Seturidze
# Chess
# User Interface / Run Loop

from files.game import *
import pygame as pg
from files.boards import Board
from files.assets import load_sprite, new_surface, Surface, tint

RAISE = False


class GUI:
    def __init__(
        self,
        board : Board,
        caption : str = 'Chussy',

        title_font_size : float = 0.5, # proporitons of each tile that is the height of the text
        caption_font_size : float = 0.3,
        plaque_opacity : int = 230, # opacity for plaques
        selection_opacity : int = 210 # alpha for selection tiles.
    ):

        self.board = board 

        self.screen = pg.display.set_mode((self.board.width, self.board.height))
        pg.display.set_caption(caption)

        colors = board.scheme
        dims = board.tile_dims

        # blocks with which we can construct plaques 
        self.blocks = {
            's' : load_sprite('tiles/Box.png', dims=dims), # single

            't' : load_sprite('tiles/Top.png', dims=dims), # top
            'b' : load_sprite('tiles/Bottom.png', dims=dims), # bottom
            'v' : load_sprite('tiles/Vertical.png', dims=dims), # vertical

            'l' : load_sprite('tiles/Left.png', dims=dims), # left
            'r' : load_sprite('tiles/Right.png', dims=dims), # right
            'h' : load_sprite('tiles/Horizontal.png', dims=dims), # horizontal


            'le' : load_sprite('tiles/LeftEdge.png', dims=dims), # left edge
            're' : load_sprite('tiles/RightEdge.png', dims=dims), # right edge
            'te' : load_sprite('tiles/TopEdge.png', dims=dims), # top edge
            'be' : load_sprite('tiles/BottomEdge.png', dims=dims), # bottom edge

            'tl' : load_sprite('tiles/TopLeft.png', dims=dims), # top left
            'bl' : load_sprite('tiles/BottomLeft.png', dims=dims), # bottom left
            'tr' : load_sprite('tiles/TopRight.png', dims=dims), # top right
            'br' : load_sprite('tiles/BottomRight.png', dims=dims), # bottom right

            'm' : load_sprite('tiles/Middle.png', dims=dims) # middle
        }


        self.title_font = pg.font.Font('files/font.ttf', int(self.board.tile_height * title_font_size))
        self.caption_font = pg.font.Font('files/font.ttf', int(self.board.tile_height * caption_font_size))

        self.checkmate_text = self.title_font.render('Checkmate', True, colors['checkmate'])
        self.stalemate_text = self.title_font.render('Stalemate', True, colors['stalemate'])

        self.plaque_opacity = plaque_opacity
        self.selection_opacity = selection_opacity

        
        self.game_over_plaque : Surface | None = None # the game over plaque, we construct it upon the first game over
        self.reset_button = self.caption_font.render('Reset', True, colors['text'])
        self.close_button = self.caption_font.render('Quit', True, colors['text'])

        self.reset_center = None 
        self.close_center = None 

        self.mouse_dragging = None 

        self.game_over_screen = None  
        self.game_over_rect = None 
    
    # constructs a plaque using blocks sprites
    # width and height are the dimensions of the plaque in terms of tiles, 
    # i.e. 3x5 would return a 3 tile by 5 tile plaque
    def new_plaque(self, width : int, height : int, color : Color, opacity : int = 255):
        tile_w = self.board.tile_width
        tile_h = self.board.tile_height

        # special cases if any of the dimensions are one
        if width == 1 and height == 1:
            return tint(self.blocks['s'].copy(), color=color, opacity=opacity)
        
        if width == 1:
            surface = new_surface((tile_w, height * tile_h))

            t = self.blocks['t']
            b = self.blocks['b']
            v = self.blocks['v']

            surface.blit(t, (0, 0))
            surface.blit(b, (0, (height-1)*tile_h))

            for i in range(1, height-1):
                surface.blit(v, (0, i*tile_h))
            
            return tint(surface, color=color, opacity = opacity)

        if height == 1:
            surface = new_surface((width * tile_w, tile_h))

            l = self.blocks['l']
            r = self.blocks['r']
            h = self.blocks['h']

            surface.blit(l, (0, 0))
            surface.blit(r, ((width-1)*tile_w, 0))

            for i in range(1, width-1):
                surface.blit(h, (i*tile_w, 0))
            
            return tint(surface, color=color, opacity = opacity)

        # otherwise: 
        surface = new_surface((width * tile_w, height * tile_h))

        tl = self.blocks['tl']
        bl = self.blocks['bl']
        tr = self.blocks['tr']
        br = self.blocks['br']

        BOTTOM = (height-1) * tile_h 
        RIGHT = (width-1) * tile_w 

        surface.blit(tl, (0, 0))
        surface.blit(bl, (0, BOTTOM))
        surface.blit(tr, (RIGHT, 0))
        surface.blit(br, (RIGHT, BOTTOM))

        te = self.blocks['te']
        be = self.blocks['be']
        le = self.blocks['le']
        re = self.blocks['re']
        
        for i in range(1, width-1):
            I = i * tile_w 
            surface.blit(te, (I, 0))
            surface.blit(be, (I, BOTTOM))
        
        for i in range(1, height-1):
            I = i * tile_h 
            surface.blit(le, (0, I))
            surface.blit(re, (RIGHT, I))
        
        m = self.blocks['m']
        for i in range(1, width-1):
            for j in range(1, height-1):
                surface.blit(m, (i * tile_w, j * tile_h))
        
        return tint(surface, color=color, opacity=opacity)

    # constructs the game over screen
    def construct_game_over_screen(self, text : pg.surface.Surface):
        if self.game_over_plaque is None:
            self.game_over_plaque = self.new_plaque(width=5, height=3, color=self.board.scheme['plaque'], opacity=self.plaque_opacity)

        plaque = self.game_over_plaque.copy()
        plaque_rect = plaque.get_rect()
        x, y = plaque_rect.center
        Xmid, Ymid = self.board.center

        dx_r = plaque_rect.width // 5
        dx_q = plaque_rect.width // 4
        dy = plaque_rect.height // 7

        title_rect = text.get_rect()
        title_rect.center = (x, y - dy)

        plaque.blit(text, title_rect)

        new_button = self.reset_button
        new_button_rect = new_button.get_rect()
        new_button_rect.center = (x - dx_r, y + dy)

        if self.reset_center is None:
            self.reset_center = (Xmid - dx_r, Ymid + dy)

        plaque.blit(new_button, new_button_rect)

        quit_button = self.close_button
        quit_button_rect = quit_button.get_rect()
        quit_button_rect.center = (x + dx_q, y + dy)

        if self.close_center is None:
            self.close_center = (Xmid + dx_q, Ymid + dy)

        plaque.blit(quit_button, quit_button_rect)

        self.game_over_screen = plaque 
        plaque_rect.center = self.board.center
        self.game_over_rect = plaque_rect

    # returns true if the given position clicks the given square
    def hits(self, pos, size, center):
        w = (size[0]+1)//2
        h = (size[1]+1)//2 

        x, y = pos 

        X, Y = center 

        return (X - w <= x <= X + w) and (Y - h <= y <= Y + h)
    

    def ingame_event_loop(self, vars : dict) -> List[str]:
        developments = []

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
                            developments = self.board.game.move(selected, target)
                        except Exception as e:
                            if not RAISE:
                                self.board.sounds['illegal'].play()
                                print(e)
                            else:
                                raise 
                            
                    
                    self.board.deselect()
        
        return developments 
            
    def game_over_event_loop(self, vars : dict) -> List[str]:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                vars['running'] = False
            
            if event.type == pg.MOUSEBUTTONDOWN:
                vars['click_pos'] = event.pos
            
            if event.type == pg.MOUSEBUTTONUP and vars['click_pos'] is not None:
                # IF RESET
                reset_size = self.reset_button.get_rect().size
                reset_center = self.reset_center

                quit_size = self.close_button.get_rect().size 
                quit_center = self.close_center

                if self.hits(vars['click_pos'], reset_size, reset_center) and self.hits(event.pos, reset_size, reset_center): 
                    sound = self.board.begin()
                    self.game_over_screen = None
                    self.game_over_rect = None 
                    sound.play()
                elif self.hits(vars['click_pos'], quit_size, quit_center) and self.hits(event.pos, quit_size, quit_center):
                    vars['running'] = False
        
        return []
                

    # flips a frame given the variables and developments
    def frame(self, developments : List[str]):
        image, sounds = self.board.update(developments, pg.mouse.get_pos())

        self.screen.blit(image, (0,0))
        for sound in sounds:
            sound.play()

        promoting = self.board.game.promoting
        if promoting is not None:
            figs = promoting.promotion_list
            if len(figs) == 1:
                    sound_keys = self.board.game.promote(figs[0])
                    # if the player is out of legal moves, the game ends
                    for sound_key in sound_keys:
                        self.board.sounds[sound_key].play()
            else:
                # WRITE THIS!
                return
        
        game_over = self.board.game.game_over

        if game_over != 0:
            if self.game_over_screen is None:
                self.construct_game_over_screen(self.checkmate_text if game_over == 1 else self.stalemate_text)
            
            self.screen.blit(self.game_over_screen, self.game_over_rect)

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
            if not self.board.game.game_over:
                developments = self.ingame_event_loop(vars)
            else:
                developments = self.game_over_event_loop(vars)

            self.frame(developments)

            




