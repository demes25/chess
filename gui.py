from game import *
import pygame as pg


Color = Tuple[int, int, int]

class BoardScreen:
    def __init__(
        self,
        game : Game,
        dims : Tuple[int, int],
        colors : Tuple[Color, Color] = ((250, 242, 210), (90, 50, 35)),
        player_colors : List[Color] = [(160, 132, 120), (40, 15, 10)],
        caption : str = 'Chussy'
    ):
        # TODO: generalize
        assert game.rank == 2
        assert len(game.players) == 2

        self.game = game 

        self.center = (dims[0]//2, dims[1]//2)

        self.screen = pg.display.set_mode(dims)
        pg.display.set_caption(caption)

        self.COLS, self.ROWS = game.board.shape

        self.width, self.height = dims 

        self.tile_W = self.width // self.COLS
        self.tile_H = self.height // self.ROWS

        self.colors = colors 

        self.font = pg.font.Font(None, int(self.tile_H * 0.8))

        self.player_colors = player_colors if player_colors else colors

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
        self.draw_piece(piece, self.font.render(piece.figure.name , True, color))


    # TODO: introduce sprites
    def draw_names(self):
        for i in range(len(self.game.players)):
            player = self.game.players[i]
            color = self.player_colors[i]

            self.draw_name(player.general, color)

            for piece in player.army:
                self.draw_name(piece, color)
            
    
    def draw(self):
        self.draw_board()
        self.draw_names()

    def show(self):
        pg.display.flip()

    def update(self, development):
        self.draw()

        # NOTE: hardcoded, TODO: generalize
        if development > 2:
            if development == 3:
                text = self.font.render('Checkmate', True, (214, 89, 50))
            elif development == 4:
                text = self.font.render('Stalemate', True, (125, 89, 50))

            rect = text.get_rect()
            rect.center = self.center 
            self.screen.blit(text, rect)
        
        self.show()


    def run(self):
        running = True 
        development = 0
        while running:
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
                                print(e)
                                
                        
                        self.held_piece = None

            self.update(development)

