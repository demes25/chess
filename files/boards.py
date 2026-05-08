# Demetre Seturidze
# Chess
# Boards

from files.game import *
from abc import ABC, abstractmethod
from files.assets import Sound, Surface, Scheme, SFX, DefaultScheme, DefaultSFX
from files.assets import load_sprite, tint

xhat = np.array([1, 0])
yhat = np.array([0, 1])

class Board(ABC):
    def __init__(
        self, 
        tile_dims : Tuple[int, int],
        dimensions : List[int] = [8, 8], 
        num_players : int = 2,

        scheme : Scheme = DefaultScheme, # the color scheme
        sounds : SFX = DefaultSFX,
        sprite_size : float = 0.95 # proportion of each tile that the sprite takes up.
    ):
        self.num_players = num_players

        self.dimensions = dimensions
        self.rank = len(dimensions)

        # TODO: generalize tile dimensions and board rank. right now only supports rank-2 [n x m] boards
        # and 2 players
        assert len(dimensions) == 2
        assert num_players == 2

        self.scheme = scheme
        self.sounds = sounds

        self.tile_width, self.tile_height = self.tile_dims = tile_dims 

        tile = load_sprite('tiles/Tile.png', dims=tile_dims)

        white_tile = tint(tile.copy(), color=scheme['tile_white'])
        black_tile = tint(tile.copy(), color=scheme['tile_black'])

        self.tiles = (white_tile, black_tile) # the tiles - colored square surfaces

        self.figure_width = int(self.tile_width * sprite_size) # figure sprite width
        self.figure_height = int(self.tile_height * sprite_size) # figure sprite height
        self.figure_dims = (self.figure_width, self.figure_height)

        self.game = None
        
        self.COLS, self.ROWS = self.dimensions = dimensions
        self.width = self.COLS * self.tile_width
        self.height = self.ROWS * self.tile_height 

        self.surface = Surface((self.width, self.height))
        self.center = (self.width//2, self.height//2)
        self.selected_piece = None 


    # translates a point on the screen to a square on the board
    def board_pos(self, coords : tuple):
        i, j = coords 

        return i // self.tile_width, (self.height - j) // self.tile_height

    # translates a square on the board to its center point on the screen
    def coords(self, board_pos : tuple):
        I, J = board_pos

        i = int(self.tile_width * (I + 0.5))
        j = int(self.height - (J + 0.5)*self.tile_height)

        return i, j 

    # "selects" the piece 
    def select(self, coords : tuple):
        self.selected_piece = self.game.at(self.board_pos(coords))
    
    def deselect(self):
        self.selected_piece = None 

    # begins the game, returns the start sound effect
    def begin(self) -> Sound:
        self.game = self.__call__()
        self.game.game_over = 0 
        self.game_over_screen = None 
        return self.sounds['start']

    # draws the board
    def draw_board(self):
        W = self.tile_width
        H = self.tile_height

        for i in range(self.ROWS):
            for j in range(self.COLS):
                # Alternate color based on position
                tile = self.tiles[(i+j) % 2]

                self.surface.blit(tile, (j * W, i * H))
    
    # draws the piece at the corresponding square
    def draw_piece(self, piece : Piece, coords : Tuple[int, int] | None = None):
        sprite = piece.figure.sprite
        rect = sprite.get_rect()
        rect.center = coords if coords is not None else self.coords(piece.position)
        self.surface.blit(sprite, rect) 
    
    # draws all pieces. held_coords is the coordinate of the center of the held piece.
    # if it is None, we assume that the piece has not been "picked up" and we draw it on its square.
    def draw_pieces(self, held_coords : Tuple[int, int] | None = None):
        if not self.game:
            return
        
        for piece in self.game.pieces.values():
            if piece is not self.selected_piece:
                self.draw_piece(piece)
        
        if self.selected_piece is not None:
            self.draw_piece(self.selected_piece, held_coords)
    
    # draws the board to its surface
    def draw(self, held_coords : Tuple[int, int] | None = None):
        self.draw_board()
        self.draw_pieces(held_coords=held_coords)

    # returns the surface image and a list of sounds according to the list of developments
    # also updates its internal state depending on developments
    def update(self, developments : List[str], held_coords : Tuple[int, int] | None = None) -> Tuple[Surface, List[Sound]]:
        self.draw(held_coords)
        
        sounds = [self.sounds[development] for development in developments]
        return self.surface, sounds
        
    #should return a Game object with a chess game on this set
    @abstractmethod
    def __call__(self) -> Game:
        pass

class Moves:
    @staticmethod 
    def Perimeter() -> Move:
        return Discrete([(1, 0), (0, 1), (-1, 0), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)])

    @staticmethod
    def DiagonalStep() -> Move:
        return Discrete([(1, 1), (1, -1), (-1, 1), (-1, -1)])
    
    @staticmethod
    def OrthogonalStep() -> Move:
        return Discrete([(1, 0), (0, 1), (-1, 0), (0, -1)])
    
    # we create a special move: castle   
    @staticmethod
    def Castle() -> Move:         
        def castle_validity(game : Game, end : Vector) -> bool:
            return True 
        
        # TODO: generalize castling to larger boards/higher dimensions
        def castle_condition(game : Game, start : Vector, end : Vector) -> bool:
            # we want to ensure that 
            # a) neither the king nor the rook have moved, nor is there check
            # b) nothing blocks the path
            # c) nothing checks the path
            sign = (end - start)[0] > 0
            dir = xhat if sign else -xhat

            # checks moves and whether we are in check
            king = game.at(start)
            if king is None or king.has_moved or king.player.is_in_check:
                return False
            
            rook_pos = np.array([7, start[1]]) if sign else np.array([0, start[1]])
            rook = game.at(rook_pos)
            if rook is None or rook.has_moved:
                return False
            
            # start iterating: if any square is occupied or seen by a piece, we return false. 
            vec = start + dir
            while game.in_bounds(vec):
                if vec[0] != rook_pos[0] and game.at(vec) is not None:
                    return False
                
                for player in game.players:
                    if player is not king.player:
                        for monarch in player.monarchs:
                            if game.sees(monarch, vec):
                                return False
                        
                        for piece in player.army:
                            if game.sees(piece, vec):
                                return False
                
                vec = vec + dir
            
            return True
                
        def castle_exec(game : Game, piece : Piece, target : Vector) -> bool:
            sign = (target - piece.vector)[0] > 0
            rook_pos = np.array([7, piece.vector[1]]) if sign else np.array([0, piece.vector[1]])
            dir = xhat if sign else -xhat

            init_pos = piece.vector
            rook = game.at(rook_pos)

            Move.generalized_execute(game, piece, init_pos + 2*dir)
            Move.generalized_execute(game, rook, init_pos + dir)

            return False

        return Discrete([(-2, 0), (2, 0), (-3, 0), (3, 0), (-4, 0), (4, 0), (-5, 0), (5, 0)], captures = False, special_condition=castle_condition, special_exec=castle_exec, special_validity=castle_validity)
        
    # we create a special move: en passant
    @staticmethod
    def EnPassant(forward : int) -> Move:

        forward_direction = np.array([0, forward])
        
        def passant_validity(game : Game, end : Vector) -> bool:
            piece = game.at(end - forward_direction) 
            # make sure the pawn did a leap
            if piece is not None and abs(piece.history[0][1] - piece.history[-1][1]) == 2:
                return piece.figure.name == 'Pawn' and piece.just_first
            return False 
        
        def passant_condition(game : Game, start : Vector, end : Vector) -> bool:
            return passant_validity(game, end)
        
        def passant_exec(game : Game, piece : Piece, target : Vector) -> bool:
            return Move.generalized_execute(game, piece, end_pos = target, kill_target = target-forward_direction)

        return Discrete([(-1, forward), (1, forward)], moves = False, special_condition=passant_condition, special_exec=passant_exec, special_validity=passant_validity)
    
    @staticmethod
    def PawnPush(forward : int) -> Move:
        return Discrete([(0, forward)], captures=False)
    
    @staticmethod
    def PawnJump(forward : int) -> Move:
        return Discrete([(0, 2*forward)], captures=False)
    
    @staticmethod
    def PawnTake(forward : int) -> Move:
        return Discrete([(-1, forward), (1, forward)], moves=False)
        
    @staticmethod
    def KnightLeap() -> Move:
        return Discrete([(2, 1), (1, 2), (-1, 2), (-2, 1), (2, -1), (1, -2), (-2, -1), (-1, -2)])

    @staticmethod 
    def AlfilLeap() -> Move:
        return Discrete([(2, 2), (2, -2), (-2, 2), (-2, -2)])
    
    @staticmethod
    def DabaabaLeap() -> Move:
        return Discrete([(2, 0), (0, 2), (-2, 0), (0, -2)])

    @staticmethod
    def OrthogonalSpan() -> Move:
        return Spanning([(0, 1), (1, 0)])
    
    @staticmethod
    def DiagonalSpan() -> Move:
        return Spanning([(1, 1), (1, -1)])

# here we store moves and figures for Standard Chess.
# we also have a "constructor" (__call__) which gives us the full game
class Chess(Board): 
    def __init__(
        self, 
        tile_dims : Tuple[int, int],

        scheme : Scheme = DefaultScheme,
        sounds : SFX = DefaultSFX,

        sprite_size : float = 0.95
    ):
        super().__init__(tile_dims, dimensions=[8, 8], num_players=2, scheme=scheme, sounds=sounds, sprite_size=sprite_size)

        self.White : Dict[str, Figure] = {
            'K' : Figure(
                name = 'King', 
                value = 0, 
                color = scheme['player_white'], 
                dims = self.figure_dims,
                moves = [
                    Moves.Perimeter()
                ],
                first = [
                    Moves.Castle()
                ]
            ),

            'Q' : Figure(
                name = 'Queen', 
                value = 9, 
                color = scheme['player_white'], 
                dims = self.figure_dims,
                moves = [
                    Moves.OrthogonalSpan(), Moves.DiagonalSpan()
                ]
            ),

            'R' : Figure(
                name = 'Rook',
                value = 5,
                color = scheme['player_white'], 
                dims = self.figure_dims,
                moves = [
                    Moves.OrthogonalSpan()
                ]
            ),

            'B' : Figure(
                name = 'Bishop',
                value = 3,
                color = scheme['player_white'], 
                dims = self.figure_dims,
                moves = [
                    Moves.DiagonalSpan()
                ]
            ),

            'N' : Figure(
                name = 'Knight',
                value = 3,
                color = scheme['player_white'], 
                dims = self.figure_dims,
                moves = [
                    Moves.KnightLeap()
                ]
            ),

            'p' : Figure(
                name = 'Pawn',
                value = 1,
                color = scheme['player_white'], 
                dims = self.figure_dims,
                moves = [
                    Moves.PawnPush(1), Moves.PawnTake(1), Moves.EnPassant(1)
                ],
                first = [
                    Moves.PawnJump(1)
                ]
            )
        }

        self.Black : Dict[str, Figure] = {
            'K' : Figure(
                name = 'King', 
                value = 0, 
                color = scheme['player_black'], 
                dims = self.figure_dims,
                moves = [
                    Moves.Perimeter()
                ],
                first = [
                    Moves.Castle()
                ]
            ),

            'Q' : Figure(
                name = 'Queen', 
                value = 9, 
                color = scheme['player_black'], 
                dims = self.figure_dims,
                moves = [
                    Moves.OrthogonalSpan(), Moves.DiagonalSpan()
                ]
            ),

            'R' : Figure(
                name = 'Rook',
                value = 5,
                color = scheme['player_black'], 
                dims = self.figure_dims,
                moves = [
                    Moves.OrthogonalSpan()
                ]
            ),

            'B' : Figure(
                name = 'Bishop',
                value = 3,
                color = scheme['player_black'], 
                dims = self.figure_dims,
                moves = [
                    Moves.DiagonalSpan()
                ]
            ),

            'N' : Figure(
                name = 'Knight',
                value = 3,
                color = scheme['player_black'], 
                dims = self.figure_dims,
                moves = [
                    Moves.KnightLeap()
                ]
            ),

            'p' : Figure(
                name = 'Pawn',
                value = 1,
                color = scheme['player_black'], 
                dims = self.figure_dims,
                moves = [
                    Moves.PawnPush(-1), Moves.PawnTake(-1), Moves.EnPassant(-1)
                ],
                first = [
                    Moves.PawnJump(-1)
                ]
            )
        }
    

    def __call__(self):
        white_army = [
            Piece(self.White['R'], (0, 0)),
            Piece(self.White['N'], (1, 0)),
            Piece(self.White['B'], (2, 0)),
            Piece(self.White['Q'], (3, 0)),
            Piece(self.White['B'], (5, 0)),
            Piece(self.White['N'], (6, 0)),
            Piece(self.White['R'], (7, 0))
        ]

        promotes = promotes=[self.White['Q'], self.White['R'], self.White['N'], self.White['B']]
        for i in range(8):
            white_army.append(
                Piece(
                    self.White['p'], (i, 1), 
                    promotes=promotes
                )
            )
        
        black_army = [
            Piece(self.Black['R'], (0, 7)),
            Piece(self.Black['N'], (1, 7)),
            Piece(self.Black['B'], (2, 7)),
            Piece(self.Black['Q'], (3, 7)),
            Piece(self.Black['B'], (5, 7)),
            Piece(self.Black['N'], (6, 7)),
            Piece(self.Black['R'], (7, 7))
        ]
        
        promotes = [self.Black['Q'], self.Black['R'], self.Black['N'], self.Black['B']]
        for i in range(8):
            black_army.append(
                Piece(
                    self.Black['p'], (i, 6), 
                    promotes=promotes
                )
            )
        
        white = Player(
            monarch = Piece(self.White['K'], (4, 0)),
            army = white_army,
            index = 0
        )

        black = Player(
            monarch = Piece(self.Black['K'], (4, 7)),
            army = black_army,
            index = 1
        )

        return Game(self.dimensions, [white, black])

class Shatranj(Board):
    def __init__(
        self, 
        tile_dims : Tuple[int, int],

        scheme : Scheme = DefaultScheme,
        sounds : SFX = DefaultSFX,

        sprite_size : float = 0.95
    ):
        super().__init__(tile_dims, dimensions=[8, 8], num_players=2, scheme=scheme, sounds=sounds, sprite_size=sprite_size)

        self.White : Dict[str, Figure] = {
            'K' : Figure(
                name = 'King', 
                value = 0, 
                color = scheme['player_white'], 
                
                dims = self.figure_dims,
                moves = [
                    Moves.Perimeter()
                ]
            ),

            'F' : Figure(
                name = 'Ferz', 
                value = 2, 
                color = scheme['player_white'], 
                
                dims = self.figure_dims,
                moves = [
                    Moves.DiagonalStep()
                ]
            ),

            'R' : Figure(
                name = 'Rook',
                value = 5,
                color = scheme['player_white'], 
                
                dims = self.figure_dims,
                moves = [
                    Moves.OrthogonalSpan()
                ]
            ),

            'A' : Figure(
                name = 'Alfil',
                value = 2,
                color = scheme['player_white'], 
                
                dims = self.figure_dims,
                moves = [
                    Moves.AlfilLeap()
                ]
            ),

            'N' : Figure(
                name = 'Knight',
                value = 3,
                color = scheme['player_white'], 
                
                dims = self.figure_dims,
                moves = [
                    Moves.KnightLeap()
                ]
            ),

            'p' : Figure(
                name = 'Pawn',
                value = 1,
                color = scheme['player_white'], 
                
                dims = self.figure_dims,
                moves = [
                    Moves.PawnPush(1), Moves.PawnTake(1)
                ]
            )
        }

        self.Black : Dict[str, Figure] = {
            'K' : Figure(
                name = 'King', 
                value = 0, 
                color = scheme['player_black'], 
                
                dims = self.figure_dims,
                moves = [
                    Moves.Perimeter()
                ]
            ),

            'F' : Figure(
                name = 'Ferz', 
                value = 9, 
                color = scheme['player_black'], 
                
                dims = self.figure_dims,
                moves = [
                    Moves.DiagonalStep()
                ]
            ),

            'R' : Figure(
                name = 'Rook',
                value = 5,
                color = scheme['player_black'], 
                
                dims = self.figure_dims,
                moves = [
                    Moves.OrthogonalSpan()
                ]
            ),

            'A' : Figure(
                name = 'Alfil',
                value = 3,
                color = scheme['player_black'], 
                
                dims = self.figure_dims,
                moves = [
                    Moves.AlfilLeap()
                ]
            ),

            'N' : Figure(
                name = 'Knight',
                value = 3,
                color = scheme['player_black'], 
                
                dims = self.figure_dims,
                moves = [
                    Moves.KnightLeap()
                ]
            ),

            'p' : Figure(
                name = 'Pawn',
                value = 1,
                color = scheme['player_black'], 
                
                dims = self.figure_dims,
                moves = [
                    Moves.PawnPush(-1), Moves.PawnTake(-1)
                ]
            )
        }
    
    def __call__(self):
        white_army = [
            Piece(self.White['R'], (0, 0)),
            Piece(self.White['N'], (1, 0)),
            Piece(self.White['A'], (2, 0)),
            Piece(self.White['F'], (3, 0)),
            Piece(self.White['A'], (5, 0)),
            Piece(self.White['N'], (6, 0)),
            Piece(self.White['R'], (7, 0))
        ]

        for i in range(8):
            white_army.append(
                Piece(
                    self.White['p'], (i, 1), 
                    promotes=[self.White['F']]
                )
            )
        
        black_army = [
            Piece(self.Black['R'], (0, 7)),
            Piece(self.Black['N'], (1, 7)),
            Piece(self.Black['A'], (2, 7)),
            Piece(self.Black['F'], (3, 7)),
            Piece(self.Black['A'], (5, 7)),
            Piece(self.Black['N'], (6, 7)),
            Piece(self.Black['R'], (7, 7))
        ]
        
        for i in range(8):
            black_army.append(
                Piece(
                    self.Black['p'], (i, 6), 
                    promotes=[self.Black['F']] # TODO: must generalize promotion
                )
            )
        
        white = Player(
            monarch = Piece(self.White['K'], (4, 0)),
            army = white_army,
            index = 0
        )

        black = Player(
            monarch = Piece(self.Black['K'], (4, 7)),
            army = black_army,
            index = 1
        )

        return Game([8, 8], [white, black])

