# Demetre Seturidze
# Chess
# Moves

from typing import *
from abc import ABC, abstractmethod    
import numpy as np  

Vector = np.typing.NDArray[np.int_] # for typehinting - vector is a 1-d integer array

# returns the scaling of dir that yields disp. 0 if inconsistent
def scaling(dir : Vector, disp : Vector):
    if dir[0] == 0:
        return disp[1] // dir[1]
    
    k = disp[0] // dir[0]
    return k if k * dir[1] == disp[1] else 0
    

class Move(ABC):
    def __init__(
        self,

        dirs : List[tuple | Vector],

        captures : bool = True, # True if this move can be executed as a capture
        moves : bool = True # True if this move can be executed without capturing
    ): 
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
    
    # returns true if the move complex can access the start->end move
    # must be given the game object in order to evaluate this
    @abstractmethod
    def accesses(self, game, start : Vector, end : Vector):
        pass 


class Span(Move):
    def __init__(
        self,

        dirs : List[tuple | Vector],

        captures : bool = True,
        moves : bool = True,

        min_num : int = 1, # minimum number of squares to move

        min_obstacles : int = 0, # minimum number of obstacles (like for cannon in xiangqi, which needs 1)
        max_obstacles : int = 0  # maximum number of obstacles (always 0 for orthodox chess)
    ):
        super().__init__(dirs, captures, moves)

        self.min_num = min_num 
        self.min_obstacles = min_obstacles
        self.max_obstacles = max_obstacles
    
    def accesses(self, game, start : Vector, end : Vector):
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

            # if the move does not obey the established minimum number of squares, we return false
            if k < self.min_num:
                return False 

            move = sign * move 

            # check for blocks
            for _ in range(1, k+1):
                vec = vec + move 

                if not game.in_bounds(vec):
                    break
                
                pos = tuple(vec.tolist())
                if game.board[pos] != -1:
                    obstacles += 1
                
                # if we find more than the admitted amount of obstacles, return false
                if obstacles > self.max_obstacles:
                    return False 
            

            return obstacles >= self.min_obstacles

        return False  


class Leap(Move):
    