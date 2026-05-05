# Demetre Seturidze
# Chess
# Pieces

from typing import *     
import numpy as np   


Vector = np.typing.NDArray[np.int_] # for typehinting - vector is a 1-d integer array

# returns True if disp is a multiple of dir
def consistent(dir : Vector, disp : Vector):
    if dir[0] == 0:
        return disp[0] == 0
    
    k = disp[0] // dir[0]
    return k * dir[1] == disp[1]
    


# enumerates the moves that a piece can make according to:
# 1) discrete moves (one-off moves like the knight's leap)
# 2) spanning moves (continuous moves like the bishop's diagonal)
# 3) special captures (like pawn)
class Figure:
    def __init__(
        self,
        name : str,
        value : int,

        discrete : List[tuple] = [], # list of *individual* moves that a piece can make 
        spanning : List[tuple] = [], # list of *bases* for spanning moves
        
        takes : List[tuple] = [], # list of special taking moves, 
        takes_exclusive : bool = False, # True if can ONLY capture using the above moves

        first : List[tuple] = [], # list of valid first moves
        first_exclusive : bool = False, # True if can ONLY do the above first moves 
        ):

        # ensure the piece has something that it can do
        assert(discrete or spanning)

        dim = len(spanning[0] if spanning else discrete[0])

        # makes sure all moves are of equal dimensionality
        assert(
            all([len(move) == dim for move in discrete]) 
            and 
            all([len(move) == dim for move in spanning])
            and 
            all([len(move) == dim for move in takes])
        )

        self.discrete = [np.array(move) for move in discrete]
        self.spanning = [np.array(move) for move in spanning]

        self.takes = [np.array(move) for move in takes] 
        self.takes_exclusive = takes_exclusive

        self.first = [np.array(move) for move in first]
        self.first_exclusive = first_exclusive

        self.dim = dim 

        self.value = value  
        self.name = name


class Piece:
    def __init__(
        self,
        figure : Figure,
        position : tuple,

        val_func = None # a function that layers into evaluating the piece (can alter value dep on position, etc)
    ):
        self.player : 'Player' | None = None 
        self.figure = figure
        self.position = position
        self.vector = np.array(self.position)

        self.val_func = val_func
        self.dead = False

        self.has_moved = False 
        self.just_first = False 
    
    # evaluates the piece
    @property
    def value(self):
        if self.val_func is None:
            return self.figure.value
        else:
            return self.val_func(self)

    # returns the displacement vector between given square and current square
    def displacement(self, target : tuple | Vector):
        return np.array(target) - self.vector
    
    # kills this piece
    def die(self):
        assert self is not self.player.general, 'General piece cannot be captured.'
        
        self.dead = True
        self.player.material -= self.figure.value 
        self.player.army.remove(self)

    
class Player:
    def __init__(
        self,
        general : Piece, # king piece, position of king piece
        army : List[Piece], # [(piece, position)]
        index : int,

        castles : List[Tuple[tuple, tuple, tuple]] = [] # a list of castles: (starting position of castling piece, end position of general, end position of castling piece)
    ):

        self.index = index

        # NOTE: castling may be only done with spanning pieces, in a valid direction for the spanning piece,
        #       only in the case that neither the king nor the previous piece has moved before,
        #       AND in the case that no square between and including the king and castling piece is under attack
        #
        #       meaning that castling with a bishop, say, is ill-defined because it would be required to move 
        #       the bishop beforehand to get on a valid castling diagonal consistent with the bishops spanning directions
        self.castles = castles
        # TODO: castling is a bit more complicated. it is a set of special moves.
        # consider generalizing to any special moves using dictionaries.
        # include all validity checks also.

        self.general = general
        general.player = self 

        self.army = army
        for piece in army:
            piece.player = self

        self.rank = self.general.figure.dim 

        assert all(piece.figure.dim == self.rank for piece in self.army)

        self.material = sum(piece.figure.value for piece in self.army) # counts raw value for material

        self.in_check = False # keeps track if the player is in check