# Demetre Seturidze
# Chess
# Figures

from typing import Tuple
from files.moves import *
from files.assets import Color, load_sprite

Player = Type['Player']


class Figure:
    def __init__(
        self,
        name : str,
        value : int,   

        color : Color, # color of the sprite 
        dims : Tuple[int, int], # dimensions of the sprite

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
        self.sprite = load_sprite(f'figures/{name}.png', dims=dims, color=color)

class Piece:
    def __init__(
        self,
        figure : Figure,
        position : tuple,

        promotes : List['Figure'] = [], # a list of figures to which a figure may promote upon reaching the other end of the board 
        promotion_axis : int = -1 # the promotion axis
    ):
        self.player : Player | None = None 
        self.figure = figure
        self.position = position
        self.history = [position]
        self.vector = np.array(self.position)

        self.promotion_list = promotes
        self.promotion_axis = promotion_axis

        self.dead = False
        self.sprite = None

        self.has_moved = False 
        self.just_first = False 
    
    # returns the displacement vector between given square and current square
    def displacement(self, target : tuple | Vector):
        return np.array(target) - self.vector

    # adds the current position to history
    def update_history(self):
        self.history.append(self.position)
    
    # kills this piece
    def die(self):
        assert len(self.player.monarchs) > 1 or self is not self.player.monarchs[0], 'General piece cannot be captured.'
        
        self.dead = True
        self.player.material -= self.figure.value 
        try:
            self.player.army.remove(self)
        except ValueError:
            self.player.monarchs.remove(self)


    # a dynamic function that iterates through all available moves for this piece
    def available_squares(self, game):
        if not self.has_moved:
            for move in self.figure.first:
                for square in move.available_squares(game, self.vector):
                    yield square
            
            if self.figure.first_exclusive:
                return
        
        for move in self.figure.moves:
            for square in move.available_squares(game, self.vector):
                yield square
