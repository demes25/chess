from files.game import *
import pygame as pg


Color = Tuple[int, int, int]
Sound = pg.mixer.Sound

pg.init()
pg.mixer.init()

def _conditional_play(sound : Sound | None):
    if sound is not None:
        sound.play()

def _load_image(filename : str, color : Color, width : int, height : int, opacity : int = 255):
    # Make a copy so original stays unchanged
    surface = pg.image.load(filename)
    surface = pg.transform.scale(surface, (width, height))
    
    # Fill with tint color using multiply blend
    surface.fill((*color, opacity), special_flags=pg.BLEND_RGBA_MULT)
    
    return surface


# TODO: some takes don't register graphically
class GUI:
    def __init__(
        self,
        setup : Callable[[], Game],
        tile_dims : Tuple[int, int], # the size of a tile
        colors : Tuple[Color, Color] = ((250, 242, 210), (90, 50, 35)), # square colors
        player_colors : List[Color] = [(220, 192, 180), (130, 80, 70)], # player colors 

        checkmate_color : Color = (214, 45, 25), # color of the checkmate text
        stalemate_color : Color = (125, 89, 50), # color of the stalemate text

        game_over_color : Color = (170, 120, 100), # color of the game over screen
        text_color : Color = (220, 192, 180), # color of general text 

        caption : str = 'Chussy',

        sprite_size : float = 0.95, # proportion of each tile that the sprite takes up.
        title_font_size : float = 0.5, # proporitons of each tile that is the height of the text
        caption_font_size : float = 0.3 
    ):
        self.setup = setup 
        self.game = setup()
        self.game_over = False 

        # TODO: generalize
        assert self.game.rank == 2
        assert len(self.game.players) == 2 

        self.tile_W, self.tile_H = tile_dims 
        self.COLS, self.ROWS = self.game.board.shape
        self.width = self.COLS * self.tile_W
        self.height = self.ROWS * self.tile_H 

        self.screen = pg.display.set_mode((self.width, self.height))

        self.center = (self.width//2, self.height//2)

        pg.display.set_caption(caption)

        self.colors = colors 

        self.title_font = pg.font.Font('files/font.ttf', int(self.tile_H * title_font_size))
        self.caption_font = pg.font.Font('files/font.ttf', int(self.tile_H * caption_font_size))

        self.checkmate_text = self.title_font.render('Checkmate', True, checkmate_color)
        self.stalemate_text = self.title_font.render('Stalemate', True, stalemate_color)

        self.plaque = _load_image('files/sprites/plaque.png', game_over_color, 5*self.tile_W, 3*self.tile_H, opacity=210)
        self.reset_button = self.caption_font.render('Reset', True, text_color)
        self.close_button = self.caption_font.render('Quit', True, text_color)

        self.reset_center = None 
        self.close_center = None 

        self.game_over_screen = None  

        self.player_colors = player_colors if player_colors else colors

        self.sounds = {
            'move' : Sound('files/sounds/move.mp3'), 
            'take' : Sound('files/sounds/take.mp3'), 
            'check' : Sound('files/sounds/check.mp3'), 
            'start' : Sound('files/sounds/start.mp3'), 
            'end' : Sound('files/sounds/end.mp3'),
            'illegal' : Sound('files/sounds/illegal.mp3')
        }

        self.sprites = [
            _load_image(
                f'files/sprites/{piece.figure.name}.png', 
                color = self.player_colors[piece.player.index],
                width = int(sprite_size*self.tile_W),
                height = int(sprite_size*self.tile_H)
            ) 
            for piece in self.game.entities
        ]

        self.held_piece = None 

    # translates a point on the screen to a square on the board
    def board_pos(self, screen_pos : tuple):
        i, j = screen_pos 

        return i // self.tile_W, (self.height - j) // self.tile_H

    # translates a square on the board to its center point on the screen
    def screen_pos(self, board_pos : tuple):
        I, J = board_pos

        i = int(self.tile_W * (I + 0.5))
        j = int(self.height - (J + 0.5)*self.tile_H)

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
        self.game = self.setup()
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
        W = self.tile_W
        H = self.tile_H

        for i in range(self.ROWS):
            for j in range(self.COLS):
                # Alternate color based on position
                color = self.colors[(i+j) % 2]

                pg.draw.rect(
                    self.screen,
                    color,
                    (j * W, i * H, W, H)
                ) 

    # draws the piece at the corresponding square
    def draw_piece(self, piece : Piece, sprite : pg.surface.Surface):
        rect = sprite.get_rect()
        rect.center = pg.mouse.get_pos() if piece is self.held_piece else self.screen_pos(piece.position)
        self.screen.blit(sprite, rect) 
    
    def draw_name(self, piece : Piece, color : Color):
        self.draw_piece(piece, self.font.render(piece.figure.name, True, color))


    # TODO: introduce sprites
    def draw_names(self):
        for i in range(len(self.game.players)):
            player = self.game.players[i]
            color = self.player_colors[i]

            self.draw_name(player.general, color)

            for piece in player.army:
                self.draw_name(piece, color)


    def draw_pieces(self):
        held_sprite = None 

        for piece, sprite in zip(self.game.entities, self.sprites):
            if piece is self.held_piece:
                held_sprite = sprite 
            elif not piece.dead:  
                self.draw_piece(piece, sprite)
        
        if held_sprite is not None:
            self.draw_piece(self.held_piece, held_sprite)
    
    def draw(self):
        self.draw_board()
        self.draw_pieces()

    def show(self):
        pg.display.flip()

    def update(self, development):
        self.draw()

        if not self.game_over:
            if development == 'stalemate':
                self.sounds['end'].play()
                self.game_over = True 
                self._construct_game_over_screen(self.stalemate_text)
            elif development == 'checkmate':
                self.sounds['check'].play()
                self.sounds['end'].play()
                self.game_over = True 
                self._construct_game_over_screen(self.checkmate_text)
            elif development:
                _conditional_play(self.sounds.get(development, None))

        if self.game_over:
            rect = self.game_over_screen.get_rect()
            rect.center = self.center 
            self.screen.blit(self.game_over_screen, rect)
        
        self.show()

    def run(self):
        running = True 
        development = None

        click_pos = None 

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
                                    development = self.game.move(self.held_piece, target)
                                except Exception as e:
                                    _conditional_play(self.sounds.get('illegal', None))
                                    print(e)
                                    
                            
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
                            development = None 
                            self._reset()
                        elif self._is_within(click_pos, quit_size, quit_center) and self._is_within(event.pos, quit_size, quit_center):
                            running = False
                
            self.update(development)

            if not self.game_over:
                development = None

