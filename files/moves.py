# Demetre Seturidze
# Chess
# Moves

from typing import Type, List, Callable
from abc import ABC, abstractmethod    
import numpy as np  

Vector = np.typing.NDArray[np.int_] # for typehinting - vector is a 1-d integer array
Game = Type['Game'] # just for typehinting, refers to the 'Game' and 'Piece' objects defined in the game and piece modules.
Piece = Type['Piece']

# returns the scaling of dir that yields disp. 0 if inconsistent
def scaling(dir : Vector, disp : Vector):
    if dir[0] == 0:
        return disp[1] // dir[1] if disp[0] == 0 else 0
    
    k = disp[0] // dir[0]
    return k if k * dir[1] == disp[1] else 0
    
# an abstract class that encompasses all moves
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
    
    # allows us to take a piece that is not at the end position of the move.
    # also allows us to explicitly not capture anything (should be used back-end strictly, in order to avoid inconsistency)
    @staticmethod
    def generalized_execute(game : Game, piece : Piece, end_pos : tuple | Vector, kill_target : Vector | None = None) -> bool:
        if kill_target is not None:
            target_piece = game.at(kill_target)
            result = target_piece is not None
            if result:
                i = game.board[target_piece.position]
                game.board[target_piece.position] = -1
                target_piece.die()
                game.pieces.pop(i)
        else:
            result = False

        if isinstance(end_pos, np.ndarray):
            piece.vector = end_pos
            end_pos = tuple(end_pos.tolist())
        else:
            piece.vector = np.array(end_pos)

        game.board[end_pos] = game.board[piece.position]
        game.board[piece.position] = -1 

        piece.position = end_pos 
        
        return result

    # executes this move
    def execute(self, game : Game, piece : Piece, target : Vector):
        if self.special_exec:
            return self.special_exec(game, piece, target)
        else:
            return Move.generalized_execute(game, piece, target, target)

    # returns true if both: the end square is a valid square, and the move complex 'sees' the end square given the start square
    def accesses(self, game : Game, start : Vector, end : Vector):
        return self.valid_square(game, end) and self.sees(game, start, end)

    # dynamically iterates through all available squares
    @abstractmethod
    def available_squares(self, game : Game, start : Vector):
        pass

# discrete moves: leaps and steps, like knight and pawn in conventional chess, OR special moves like en passant or castle
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
            if all(disp == dir):
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
                if game.board[pos] != -1:
                    obstacles += 1
                
                # if we find more than the admitted amount of obstacles, return false
                if obstacles > self.max_obstacles:
                    return False 
            
            return obstacles >= self.min_obstacles
            
        return False  

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
                if game.board[pos] != -1:
                    obstacles += 1

                if obstacles > self.max_obstacles:
                    break

                i += 1
                vec = vec + dir 

    
# compound moves go discrete -> spanning.
# the initial discrete moves do NOT capture.
# similar to the giraffe in Tamerlane chess
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



