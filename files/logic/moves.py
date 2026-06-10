# Demetre Seturidze
# Chess
# Moves and Figures

from typing import Type, List, Callable, Tuple
from abc import ABC, abstractmethod
import numpy as np  
from itertools import product, permutations

from files.logic.serialization import Serializable

Vector = np.typing.NDArray[np.int_] # for typehinting - vector is a 1-d integer array
Matrix = np.typing.NDArray[np.int_] # matrix is a 2-d integer array
BooleanMap = np.typing.NDArray[np.bool_]

Game = Type['Game'] # just for typehinting, refers to the 'Game' and 'Piece' objects defined in the game and piece modules.
Piece = Type['Piece']

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

# TODO: make interacting moves like castle separate, and special moves like en passant separate.
# they need alternate treatment for access maps. 

# an abstract class that encompasses all moves
# TODO: serialize!
class Move(ABC):
    def __init__(
        self,

        dirs : List[tuple | Vector],

        captures : bool = True, # True if this move can be executed as a capture
        moves : bool = True, # True if this move can be executed without capturing

        special_condition : Callable[[Game, Vector, Vector], bool] | None = None, # special conditions for special moves
        special_validity : Callable[[Game, Vector], bool] | None = None, # special validity check (like for en passant)
        special_exec : Callable[[Game, Piece, Vector], bool] | None = None # special execution. returns true if captures.
    ): 
        assert dirs

        self.directions = []
        self.rank = None 

        self.captures = captures 
        self.moves = moves 

        for dir in dirs:
            if self.rank is None:
                self.rank = len(dir)
            elif len(dir) != self.rank:
                raise Exception('Inconsistent rank.')
            
            self.directions.append(np.array(dir))
        
        self.special_condition = special_condition
        self.special_validity = special_validity
        self.special_exec = special_exec
    
    # returns true if the given square is 'valid'
    # i.e. -> if occupied and cannot capture, or not occupied and must capture, then no. otherwise yes.
    def valid_square(self, game : Game, square : Vector):
        if self.special_validity:
            return self.special_validity(game, square)
        
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

        special_condition : Callable[[Game, Vector, Vector], bool] | None = None,
        special_validity : Callable[[Game, Vector], bool] | None = None, 
        special_exec : Callable[[Game, Piece, Vector], bool] | None = None,
    ):
        super().__init__(dirs=dirs, captures=captures, moves=moves, special_condition=special_condition, special_validity=special_validity, special_exec=special_exec)
    
    def sees(self, game : Game, start : Vector, end : Vector):
        disp = end - start  
        
        b = False 

        for dir in self.directions:
            if np.array_equal(disp, dir):
                b = True
                break 
        
        if b:
            return self.special_condition is None or self.special_condition(game, start, end)
        
        return False 
         
    
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
        if isinstance(displacement, np.ndarray):
            self.displacement = np.sort(np.abs(displacement))
            displacement = displacement.tolist()
        else:
            self.displacement = np.sort(np.abs(np.array(displacement)))

        # generate all signed permutations of the displacement
        dirs = []
        for p in permutations(displacement):
            for signs in product([1, -1], repeat=len(displacement)):
                dirs.append(tuple(a * s for a, s in zip(p, signs)))

        super().__init__(dirs=dirs, captures=captures, moves=moves)


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
        self.discrete = discrete_dirs


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



# -- FIGURES -- #

# a figure is a set of moves, basically, along with a name and a value

class Figure:
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
       



