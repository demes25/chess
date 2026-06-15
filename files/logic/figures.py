# Demetre Seturidze
# Chess
# Moves and Figures

from typing import Type, List, Tuple
from abc import abstractmethod
import numpy as np  
from itertools import product, permutations

from netlib.serialization import Serializable, to_native

Vector = np.typing.NDArray[np.int_] # for typehinting - vector is a 1-d integer array
Matrix = np.typing.NDArray[np.int_] # matrix is a 2-d integer array
BooleanMap = np.typing.NDArray[np.bool_]

Game = Type['Game'] # just for typehinting, refers to the 'Game' and 'Piece' objects defined in the game and piece modules.
Piece = Type['Piece']

xhat = np.array([1, 0])
yhat = np.array([0, 1])

# returns the scaling of dir that yields disp. 0 if inconsistent
def scaling(dir : Vector, disp : Vector):
    k = 0
    first = True 
    for i in range(len(dir)):
        if dir[i] == 0:
            if disp[i] != 0:
                return 0
        elif disp[i] == 0:
            if dir[i] != 0:
                return 0 
        else:
            j = disp[i]//dir[i]
            if first:
                k = j
                first = False 
            elif k != j:
                return 0
    
    return k

# returns the range of scalings of the given direction vector, starting at pos bounded by the board shape
# returns: (max subtractable, max addable)
def scaling_range(board_shape : Vector, pos : Vector, dir : Vector, large_value : int = 100) -> Tuple[int, int]:
    positive_limits = np.where(
        dir > 0,
        (board_shape - 1 - pos) // dir,
        np.where(
            dir < 0,
            pos // (-dir),
            large_value
        )
    )
    
    negative_limits = np.where(
        dir < 0,
        (board_shape - 1 - pos) // (-dir),
        np.where(
            dir > 0,
            pos // (dir),
            large_value
        )
    )

    return (np.min(negative_limits), np.min(positive_limits))


# an abstract class that encompasses all moves
class Move(Serializable):
    def __init__(
        self,

        dirs : List[tuple | Vector],

        captures : bool = True, # True if this move can be executed as a capture
        moves : bool = True, # True if this move can be executed without capturing

        capture_displacement : Vector | None = None 
        # if the capture happens elsewhere (like for en passant), 
        # one may specify the displacement vector from the target square to the capture square. 
        # if None, takes as capture on target square
    ): 
        assert dirs

        self.directions : List[Vector]= []
        self.rank = None 

        self.captures = captures 
        self.moves = moves 

        for dir in dirs:
            if self.rank is None:
                self.rank = len(dir)
            elif len(dir) != self.rank:
                raise Exception('Inconsistent rank.')
            
            self.directions.append(np.array(dir))
        
        self.dirs_native = to_native(dirs)

        self.special_execute = None
        self.capture_displacement = capture_displacement
    

    # serialization
    def to_dict(self) -> dict:
        return {
            'dirs' : self.dirs_native,
            'captures' : self.captures,
            'moves' : self.moves
        }

    # returns true if the given square is 'valid'
    # i.e. -> if occupied and cannot capture, or not occupied and must capture, then no. otherwise yes.
    def valid_square(self, game : Game, square : Vector):
        piece = game.at(square)
            
        # if the target square is not occupied and we may only take, OR if the target square is occupied and we may not take,
        # the square is not accessible.
        return (
            piece is None and self.moves
        ) or (
            piece is not None and self.captures
        )
    

        
    # returns true if the move complex 'sees' the end square given the start square
    # must be given the game object in order to evaluate this.
    @abstractmethod
    def sees(self, game : Game, start : Vector, end : Vector):
        pass 

    # returns true if both: the end square is a valid square, and the move complex 'sees' the end square given the start square
    def accesses(self, game : Game, start : Vector, end : Vector):
        return self.valid_square(game, end) and self.sees(game, start, end)

    # returns a access map:
    # a map populated with True everywhere that this move can access, zeros elsewhere
    # TODO: GAME_BOARD has 1 everywhere an opposing player is standing, -1 everywhere the attacking player is standing, and 0 else
    @abstractmethod 
    def access_map(self, game_board : Matrix, pos : tuple | Vector) -> BooleanMap:
        pass

    # dynamically iterates through all available squares
    @abstractmethod
    def available_squares(self, game : Game, start : Vector):
        pass



# discrete moves: steps, like pawn in conventional chess, OR special moves like en passant or castle
class Discrete(Move):
    def __init__(
        self, 

        dirs : List[tuple | Vector],

        captures : bool = True,
        moves : bool = True,
    ):
        super().__init__(dirs=dirs, captures=captures, moves=moves)
    
    def sees(self, game : Game, start : Vector, end : Vector):
        disp = end - start  

        for dir in self.directions:
            if np.array_equal(disp, dir):
                return True
         
    
    def available_squares(self, game : Game, start : Vector):
        for dir in self.directions:
            vec = start + dir 
            if game.in_bounds(vec) and self.accesses(game, start, vec):
                yield vec
    
    def access_map(self, occupation_map : Matrix, pos : tuple | Vector) -> BooleanMap:
        result = np.zeros_like(occupation_map, dtype=np.bool)

        for dir in self.directions:
            target = dir + pos
            index = tuple(target)
            if (occupation_map[index] == 0 and self.moves) or (occupation_map[index] == 1 and self.captures):
                result[index] = True
        
        return result 
        
        
        
                
# leaps, omnidimensional, like the knight in chess, (or even the king)
class Leap(Discrete):
    def __init__(
        self, 

        displacement : tuple | Vector,

        captures : bool = True,
        moves : bool = True,
    ):  
        # we keep a numpy array to compare against,
        # but generate permutations with a python list.
        self.displacement = np.sort(np.abs(np.array(displacement)))
        displacement = self.disp_native = to_native(self.displacement)

        # generate all signed permutations of the displacement
        dirs = []
        for p in permutations(displacement):
            for signs in product([1, -1], repeat=len(displacement)):
                dirs.append(tuple(a * s for a, s in zip(p, signs)))

        super().__init__(dirs=dirs, captures=captures, moves=moves)

    # serialization
    def to_dict(self) -> dict:
        return {
            'displacement' : self.disp_native,
            'captures' : self.captures,
            'moves' : self.moves
        }

    # returns true if end-start is a valid permutation of the leap displacement
    def sees(self, game : Game, start : Vector, end : Vector):
        disp = end - start  

        return np.array_equal(np.sort(np.abs(disp)), self.displacement)
        
    

# spanning moves: ones that follow a specific direction 
# for an unspecified amount of squares. (bishop, rook, queen in conventional chess)
class Spanning(Move):
    def __init__(
        self,

        dirs : List[tuple | Vector],

        captures : bool = True,
        moves : bool = True,

        min_num : int = 1, # minimum number of squares to move
        max_num : int = None, # maximum number of squares to move

        min_obstacles : int = 0, # minimum number of obstacles (like for cannon in xiangqi, which needs 1)
        max_obstacles : int = 0  # maximum number of obstacles (always 0 for orthodox chess)
    ):
        super().__init__(dirs=dirs, captures=captures, moves=moves)

        self.min_num = min_num 
        self.max_num = max_num 
        self.min_obstacles = min_obstacles
        self.max_obstacles = max_obstacles
    
    # serialization 
    def to_dict(self) -> dict:
        additional = {
            'min_num' : self.min_num,
            'max_num' : self.max_num,
            'min_obstacles' : self.min_obstacles,
            'max_obstacles' : self.max_obstacles
        }

        dct = super().to_dict()
        dct.update(additional)
        
        return dct

    def sees(self, game : Game, start : Vector, end : Vector):
        disp = end - start 

        for dir in self.directions:
            # check if the displacement is along the given direction 
            k = scaling(dir=dir, disp=disp)

            # if not, we keep going
            if k == 0:
                continue 
            
            obstacles = 0

            # we specify sign
            sign = 1 if k > 0 else -1
            k = sign * k

            # if the move does not obey the established minimum/maximum number of squares, we return false
            if k < self.min_num:
                return False 
            if self.max_num is not None and k > self.max_num:
                return False

            dir = sign * dir 
            vec = start

            # check for blocks
            for _ in range(k-1):
                vec = vec + dir 

                if not game.in_bounds(vec):
                    return False
                
                pos = tuple(vec.tolist())
                if not np.any(game.board[pos] < 0):
                    obstacles += 1
                
                # if we find more than the admitted amount of obstacles, return false
                if obstacles > self.max_obstacles:
                    return False 
            
            return obstacles >= self.min_obstacles
            
        return False  

    def access_map(self, occupation_map : Matrix, pos : tuple | Vector) -> BooleanMap:
        result = np.zeros_like(occupation_map, dtype=np.bool)

        map_shape = np.array(occupation_map.shape, dtype=np.int16)

        for dir in self.directions:
            neg_limit, pos_limit = scaling_range(map_shape, pos, dir)

            if self.max_num is not None:
                pos_limit = np.min(pos_limit, self.max_num)
                neg_limit = np.min(neg_limit, self.max_num) 
            
            # we start by adding.
            num_obstacles = 0
            square = pos
            for _ in range(0, pos_limit):
                square = square + dir

                index = tuple(square)
                occupation = occupation_map[index]
                if occupation != 0:
                    if num_obstacles >= self.min_obstacles and occupation == 1 and self.captures:
                        result[index] = True
                    
                    num_obstacles += 1

                    if num_obstacles > self.max_obstacles:
                        break
                elif self.moves:
                    result[index] = True

            # then we subtract
            num_obstacles = 0
            square = pos
            for _ in range(0, neg_limit):
                square = square - dir

                index = tuple(square)
                occupation = occupation_map[index]
                if occupation != 0:
                    if num_obstacles >= self.min_obstacles and occupation == 1 and self.captures:
                        result[index] = True
                    
                    num_obstacles += 1

                    if num_obstacles > self.max_obstacles:
                        break
                elif self.moves:
                    result[index] = True

        return result 
        

    def available_squares(self, game : Game, start : Vector):
        if self.max_num is None:
            def _in_bounds(i):
                return True 
        else:
            def _in_bounds(i):
                return i <= self.max_num
            
        for dir in self.directions:
            vec = start + dir
            i = 1
            obstacles = 0 # counts obstacles   

            while _in_bounds(i):
                # ensure we are in bounds
                if not game.in_bounds(vec):
                    break
                elif not self.valid_square(game, vec):
                    break
                
                if i >= self.min_num and obstacles >= self.min_obstacles:
                    yield vec

                pos = tuple(vec.tolist())
                if np.any(game.board[pos] < 0):
                    obstacles += 1

                if obstacles > self.max_obstacles:
                    break

                i += 1
                vec = vec + dir 

    
# compound moves go discrete -> spanning.
# the initial discrete moves do NOT capture.
# similar to the giraffe in Tamerlane chess
#TODO: write access map function
class Compound(Spanning):
    def __init__(
        self,

        discrete_dirs : List[tuple | Vector],
        spanning_dirs : List[tuple | Vector],

        captures : bool = True,
        moves : bool = True,

        min_num : int = 1,

        min_obstacles : int = 0,
        max_obstacles : int = 0,
    ):
        super().__init__(dirs=spanning_dirs, captures=captures, moves=moves, min_num=min_num, min_obstacles=min_obstacles, max_obstacles=max_obstacles)
        self.discrete = [np.array(dir) for dir in discrete_dirs]
        self.disc_native = to_native(self.discrete)
        
    # serialization
    def to_dict(self):
        return {
            'discrete_dirs' : self.disc_native,
            'spanning_dirs' : self.dirs_native,
            'captures' : self.captures,
            'moves' : self.moves,
            'min_num' : self.min_num,
            'min_obstacles' : self.min_obstacles,
            'max_obstacles' : self.max_obstacles
        }

    def sees(self, game : Game, start : Vector, end : Vector):
        offset = None 

        for disc in self.discrete:
            offset = start + disc 
            if game.at(offset) is None and super().sees(game, offset, end):
                return True
            
        return False
    
    def available_squares(self, game : Game, start : Vector):
        offset = None

        for disc in self.discrete:
            offset = start + disc
            for square in super().available_squares(game, offset):
                yield square


# SPECIAL MOVES :

class Castle(Discrete):
    # we create a special move: castle   
    # we may castle n steps;
    # the "restrict" parameter allows us to restrict how many squares the king must be moved in order to execute castle.
    # if restricted, it will only execute castle if the king is slid by n steps. otherwise, any k >= n steps. 
    # the condition is that the rook must be at the end of the board
    # also we need to know the board width
    def __init__(self, n : int = 2, width : int = 8, restrict : bool = False):         
        
        self.n = n
        self.width = width 
        self.restrict = restrict 

        def castle_exec(game : Game, piece : Piece, target : Vector) -> bool:
            sign = (target - piece.vector)[0] > 0
            rook_pos = np.array([width-1, piece.vector[1]]) if sign else np.array([0, piece.vector[1]])
            dir = xhat if sign else -xhat

            init_pos = piece.vector
            rook = game.at(rook_pos)

            game.generalized_execute(piece, init_pos + n*dir)
            game.generalized_execute(rook, init_pos + (n-1)*dir)

            return False

        if restrict:
            dirs = [(-n, 0), (n, 0)]
        else:
            dirs = []
            for k in range(n, (width+1)//2 + 2):
                dirs.append((-k, 0))
                dirs.append((k, 0))

        super().__init__(dirs=dirs, captures = False)
        self.special_execute = castle_exec
    
    # serialization
    def to_dict(self):
        return {
            'n' : self.n,
            'width' : self.width,
            'restrict' : self.restrict
        }
    
    def sees(self, game : Game, start : Vector, end : Vector):
        if super().sees(game, start, end):
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

            rook_pos = np.array([self.width-1, start[1]]) if sign else np.array([0, start[1]])
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
        return False 

class EnPassant(Discrete):
    # forward is either 1 or -1, the sign which constitutes "forward" motion in the y-direction
    def __init__(self, forward : int):
        super().__init__([(-1, forward), (1, forward)], moves = False)
        self.capture_displacement = np.array([0, -forward])
        self.forward = forward

    # serialization
    def to_dict(self):
        return {
            'forward' : self.forward
        }
    
    def valid_square(self, game : Game, square : Vector):
        target_pos = square + self.capture_displacement
        piece = game.at(target_pos) if game.in_bounds(target_pos) else None 
        # make sure the pawn did a leap
        if piece is not None and abs(piece.history[0][1] - piece.history[-1][1]) == 2:
            return piece.figure.name == 'Pawn' and piece.just_first
        return False 


class StandardMoves:
    @staticmethod 
    def Perimeter() -> Move:
        return Discrete([(1, 0), (0, 1), (-1, 0), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)])

    @staticmethod
    def DiagonalStep() -> Move:
        return Discrete([(1, 1), (1, -1), (-1, 1), (-1, -1)])
    
    @staticmethod
    def OrthogonalStep() -> Move:
        return Discrete([(1, 0), (0, 1), (-1, 0), (0, -1)])
    
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
        return Leap((1, 2))

    @staticmethod
    def CamelLeap() -> Move:
        return Leap((1, 3))
    
    @staticmethod 
    def AlfilLeap() -> Move:
        return Leap((2, 2))
    
    @staticmethod
    def DabaabaLeap() -> Move:
        return Leap((0, 2))

    @staticmethod
    def OrthogonalSpan() -> Move:
        return Spanning([(0, 1), (1, 0)])
    
    @staticmethod
    def DiagonalSpan() -> Move:
        return Spanning([(1, 1), (1, -1)])


# -- FIGURES -- #

# a figure is a set of moves, basically, along with a name and a value

class Figure(Serializable):
    def __init__(
        self,
        name : str,
        value : int,   

        moves : List[Move] = [], # list of valid moves
    
        first : List[Move] = [], # list of valid first moves
        first_exclusive : bool = False, # True if can ONLY do the above first moves 
        ):

        # ensure the piece has something that it can do
        assert moves

        dim = moves[0].rank

        # makes sure all moves are of equal dimensionality
        assert all(move.rank == dim for move in moves) 

        self.moves = moves
        self.first = first 
        self.first_exclusive = first_exclusive

        self.dim = dim 

        self.value = value  
        self.name = name
    
    # serialization
    def to_dict(self) -> dict:
        return {
            'name' : self.name,
            'value' : self.value,

            'moves' : self.moves,

            'first' : self.first,
            'first_exclusive' : self.first_exclusive
        }
    
    def access_map(self, occupation_map : Matrix, pos : tuple | Vector, first_move : bool = False) -> BooleanMap:
        result = np.zeros_like(occupation_map, dtype=np.bool)

        if first_move:
            for f in self.first:
                result = result | f.access_map(occupation_map, pos)
        
            if self.first_exclusive:
                return result
        
        for f in self.moves:
            result = result | f.access_map(occupation_map, pos)
        
        return result 
       
Figures = {
    'King' : Figure(
        name = 'King', 
        value = 0, 
        moves = [
            StandardMoves.Perimeter()
        ],
        first = [
            Castle(n=2, width=8, restrict=False)
        ]
    ),

    'Queen' : Figure(
        name = 'Queen', 
        value = 9, 
        moves = [
            StandardMoves.OrthogonalSpan(), StandardMoves.DiagonalSpan()
        ]
    ),

    'Rook' : Figure(
        name = 'Rook',
        value = 5,
        moves = [
            StandardMoves.OrthogonalSpan()
        ]
    ),

    'Bishop' : Figure(
        name = 'Bishop',
        value = 3,
        moves = [
            StandardMoves.DiagonalSpan()
        ]
    ),

    'Knight' : Figure(
        name = 'Knight',
        value = 3,
        moves = [
            StandardMoves.KnightLeap()
        ]
    ),

    

    'ShatranjKing' : Figure(
        name = 'King',
        value = 0,
        moves = [StandardMoves.Perimeter()]
    ),

    'Ferz' : Figure(
        name = 'Ferz', 
        value = 2, 
        moves = [
            StandardMoves.DiagonalStep()
        ]
    ),

    'Alfil' : Figure(
        name = 'Alfil',
        value = 2,
        moves = [
            StandardMoves.AlfilLeap()
        ]
    ),



    'WildebeestKing' : Figure(
        name = 'King',
        value = 0,
        moves = [
            StandardMoves.Perimeter()
        ],
        first = [
            Castle(n=2, width=11, restrict=True),
            Castle(n=3, width=11, restrict=True),
            Castle(n=4, width=11, restrict=True)
        ]
    ),
    
    'Wildebeest' : Figure(
        name = 'Wildebeest',
        value = 5,
        moves=[StandardMoves.KnightLeap(), StandardMoves.CamelLeap()]
    ),

    'Camel' : Figure(
        name = 'Camel',
        value = 3,
        moves=[StandardMoves.CamelLeap()]
    ),



    'ShatranjWhitePawn' : Figure(
        name = 'Pawn',
        value = 1,
        moves = [
            StandardMoves.PawnPush(1), StandardMoves.PawnTake(-1)
        ]
    ),

    'ShatranjBlackPawn' : Figure(
        name = 'Pawn',
        value = 1,
        moves = [
            StandardMoves.PawnPush(-1), StandardMoves.PawnTake(-1)
        ]
    ),

    'WhitePawn' : Figure(
        name = 'Pawn',
        value = 1,
        moves = [
            StandardMoves.PawnPush(1), StandardMoves.PawnTake(1), EnPassant(1)
        ],
        first = [
            StandardMoves.PawnJump(1)
        ]
    ),

    'BlackPawn' : Figure(
        name = 'Pawn',
        value = 1,
        moves = [
            StandardMoves.PawnPush(-1), StandardMoves.PawnTake(-1), EnPassant(-1)
        ],
        first = [
            StandardMoves.PawnJump(-1)
        ]
    )
}
