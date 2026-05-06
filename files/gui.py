from files.game import *
import pygame as pg
from files.sets import GameSet
from files.graphics import Scheme, Default, load_sprite
Sound = pg.mixer.Sound

pg.init()
pg.mixer.init()

RAISE = False


# TODO: some takes don't register graphically
class GUI:
    def __init__(
        self,
        chess_set : GameSet,
        caption : str = 'Chussy',

        title_font_size : float = 0.5, # proporitons of each tile that is the height of the text
        caption_font_size : float = 0.3 
    ):
        self.set = chess_set
        self.game = chess_set()
        self.game_over = False 

        # TODO: generalize
        assert self.game.rank == 2
        assert len(self.game.players) == 2 

        self.COLS, self.ROWS = self.game.board.shape
        self.width = self.COLS * self.set.tile_width
        self.height = self.ROWS * self.set.tile_height 

        self.screen = pg.display.set_mode((self.width, self.height))

        self.center = (self.width//2, self.height//2)

        pg.display.set_caption(caption)

        colors = self.set.scheme
        self.board_colors = (colors['tile_white'], colors['tile_black'])

        self.title_font = pg.font.Font('files/font.ttf', int(self.set.tile_height * title_font_size))
        self.caption_font = pg.font.Font('files/font.ttf', int(self.set.tile_height * caption_font_size))

        self.checkmate_text = self.title_font.render('Checkmate', True, colors['checkmate'])
        self.stalemate_text = self.title_font.render('Stalemate', True, colors['stalemate'])

        self.plaque = load_sprite('files/sprites/plaque.png', colors['game_over'], 5*self.set.tile_width, 3*self.set.tile_height, opacity=210)
        self.reset_button = self.caption_font.render('Reset', True, colors['text'])
        self.close_button = self.caption_font.render('Quit', True, colors['text'])

        self.reset_center = None 
        self.close_center = None 

        self.game_over_screen = None  

        self.sounds = {
            'move' : Sound('files/sounds/move.mp3'), 
            'take' : Sound('files/sounds/take.mp3'), 
            'check' : Sound('files/sounds/check.mp3'), 
            'start' : Sound('files/sounds/start.mp3'), 
            'end' : Sound('files/sounds/end.mp3'),
            'illegal' : Sound('files/sounds/illegal.mp3'),
            'castle' : Sound('files/sounds/castle.mp3'),
            'promote' : Sound('files/sounds/promote.mp3')
        }

        self.held_piece = None 

    # translates a point on the screen to a square on the board
    def board_pos(self, screen_pos : tuple):
        i, j = screen_pos 

        return i // self.set.tile_width, (self.height - j) // self.set.tile_height

    # translates a square on the board to its center point on the screen
    def screen_pos(self, board_pos : tuple):
        I, J = board_pos

        i = int(self.set.tile_width * (I + 0.5))
        j = int(self.height - (J + 0.5)*self.set.tile_height)

        return i, j 

    # constructs the game over screen
    def _construct_game_over_screen(self, text : pg.surface.Surface):
        plaque = self.plaque.copy()
        plaque_rect = plaque.get_rect()
        x, y = plaque_rect.center

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
            self.reset_center = (self.width // 2 - dx_r, self.height // 2 + dy)

        plaque.blit(new_button, new_button_rect)

        quit_button = self.close_button
        quit_button_rect = quit_button.get_rect()
        quit_button_rect.center = (x + dx_q, y + dy)

        if self.close_center is None:
            self.close_center = (self.width // 2 + dx_q, self.height // 2 + dy)

        plaque.blit(quit_button, quit_button_rect)

        self.game_over_screen = plaque 
    
    # resets the game
    def _reset(self):
        self.game = self.set()
        self.game_over = False 
        self.game_over_screen = None 

    # returns true if the given position clicks the reset button
    def _is_within(self, pos, size, center):
        w = (size[0]+1)//2
        h = (size[1]+1)//2 

        x, y = pos 

        X, Y = center 

        return (X - w <= x <= X + w) and (Y - h <= y <= Y + h)

    # draws the board
    def draw_board(self):
        W = self.set.tile_width
        H = self.set.tile_height

        for i in range(self.ROWS):
            for j in range(self.COLS):
                # Alternate color based on position
                color = self.board_colors[(i+j) % 2]

                pg.draw.rect(
                    self.screen,
                    color,
                    (j * W, i * H, W, H)
                ) 

    # draws the piece at the corresponding square
    def draw_piece(self, piece : Piece):
        sprite = piece.figure.sprite
        rect = sprite.get_rect()
        rect.center = pg.mouse.get_pos() if piece is self.held_piece else self.screen_pos(piece.position)
        self.screen.blit(sprite, rect) 

    def draw_pieces(self):
        for piece in self.game.pieces.values():
            if piece is self.held_piece:
                continue
            self.draw_piece(piece)
        
        if self.held_piece is not None and not self.held_piece.dead:
            self.draw_piece(self.held_piece)
    
    def draw(self):
        self.draw_board()
        self.draw_pieces()

    def show(self):
        pg.display.flip()

    def update(self, developments):
        self.draw()

        if developments and not self.game_over:
            if 'end' in developments:
                self.game_over = True 
                self._construct_game_over_screen(self.checkmate_text if 'check' in developments else self.stalemate_text)
            for development in developments:
                self.sounds[development].play()

        if self.game_over:
            rect = self.game_over_screen.get_rect()
            rect.center = self.center 
            self.screen.blit(self.game_over_screen, rect)
        
        self.show()

    def run(self):
        running = True 
        developments = []

        click_pos = None 
        self.sounds['start'].play()

        while running:
            if not self.game_over:
                for event in pg.event.get():
                    if event.type == pg.QUIT:
                        running = False
                    
                    if event.type == pg.MOUSEBUTTONDOWN:
                        self.held_piece = self.game.at(self.board_pos(event.pos))
                    
                    if event.type == pg.MOUSEBUTTONUP:
                        if self.held_piece is not None:
                            target = self.board_pos(event.pos)

                            if target != self.held_piece.position:
                                try:
                                    developments = self.game.move(self.held_piece, target)
                                except Exception as e:
                                    if not RAISE:
                                        self.sounds['illegal'].play()
                                        print(e)
                                    else:
                                        raise 
                                    
                            
                            self.held_piece = None

            else:
                for event in pg.event.get():
                    if event.type == pg.QUIT:
                        running = False
                    
                    if event.type == pg.MOUSEBUTTONDOWN:
                        click_pos = event.pos
                    
                    if event.type == pg.MOUSEBUTTONDOWN:
                        # IF RESET
                        reset_size = self.reset_button.get_rect().size
                        reset_center = self.reset_center

                        quit_size = self.close_button.get_rect().size 
                        quit_center = self.close_center

                        if self._is_within(click_pos, reset_size, reset_center) and self._is_within(event.pos, reset_size, reset_center):
                            developments = [] 
                            self._reset()
                            self.sounds['start'].play()
                        elif self._is_within(click_pos, quit_size, quit_center) and self._is_within(event.pos, quit_size, quit_center):
                            running = False
                
            self.update(developments)

            if not self.game_over:
                developments = []

            if self.game.promoting is not None:
                figs = self.game.promoting.figure.promotes
                if len(figs) == 1:
                    self.game.promote(figs[0])
                else:
                    # WRITE THIS!
                    continue

