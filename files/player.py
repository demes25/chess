# Demetre Seturidze
# Chess
# Players

from files.figure import *

class Player:
    def __init__(
        self,
        monarch : Piece, # king piece
        army : List[Piece], 
        index : int,
    ):

        self.index = index

        self.monarchs = [monarch]
        monarch.player = self 

        self.army = army
        for piece in army:
            piece.player = self

        self.rank = monarch.figure.dim 

        assert all(piece.figure.dim == self.rank for piece in self.army)

        self.material = sum(piece.figure.value for piece in self.army) # counts raw value for material

        self.is_in_check : bool = False # keeps track if the player is in check