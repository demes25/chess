# Demetre Seturidze
# Chess
# Boards

from typing import Type, Dict, Tuple, List
from files.logic.figures import Figures
from files.logic.serialization import Serializable
from files.logic.game import Game, Piece, Player

import numpy as np
from abc import ABC, abstractmethod

# TODO: Make sets instantiable instead of fixed classes

# we define a *set*. i.e. a set of dimensions and starting armies for each player.
class Set(Serializable):
    
    def __init__(
        self, 
        
        dimensions : List[int],

        # each of these is a list of (figure_name, position)
        white_monarchs : List[Tuple[str, tuple]], 
        white_pieces : List[Tuple[str, tuple]],
        # each of these is (figure_name, position, promotion_list)
        white_pawns : List[Tuple[str, tuple, List[str]]],

        black_monarchs : List[Tuple[str, tuple]],
        black_pieces : List[Tuple[str, tuple]],
        black_pawns : List[Tuple[str, tuple, List[str]]]
    ):
        self.dimensions = dimensions

        self.white_monarchs = white_monarchs
        self.white_pieces = white_pieces
        self.white_pawns = white_pawns

        self.black_monarchs = black_monarchs
        self.black_pieces = black_pieces 
        self.black_pawns = black_pawns 

    # serialization
    def to_dict(self):
        return {
            'dimensions' : self.dimensions,
            
            'white_monarchs' : self.white_monarchs,
            'white_pieces' : self.white_pieces,
            'white_pawns' : self.white_pawns,

            'black_monarchs' : self.black_monarchs,
            'black_pieces' : self.black_pieces,
            'black_pawns' : self.black_pawns
        }

    def __call__(self) -> Game:
        white_monarchs = [
            Piece(*args) for args in self.white_monarchs
        ]
        white_pieces = [
            Piece(*args) for args in self.white_pieces
        ]
        white_pawns = [
            Piece(*args) for args in self.white_pawns
        ]


        black_monarchs = [
            Piece(*args) for args in self.black_monarchs
        ]
        black_pieces = [
            Piece(*args) for args in self.black_pieces
        ]
        black_pawns = [
            Piece(*args) for args in self.black_pawns
        ]

        white = Player(monarchs=white_monarchs, army=white_pieces + white_pawns, index=0)
        black = Player(monarchs=black_monarchs, army=black_pieces + black_pawns, index=1)

        return Game(self.dimensions, [white, black], history=[[]])

# a chess set
chess_pieces = ['Rook', 'Knight', 'Bishop', 'Queen']
chess_promotion = ['Queen', 'Rook', 'Bishop', 'Knight']
Chess = Set(
    dimensions=[8, 8],

    white_monarchs=[('King', (4, 0))],
    white_pieces=[
        (chess_pieces[i], (i, 0)) if i < 4 else (chess_pieces[6-i], (i+1, 0)) for i in range(7)
    ],
    white_pawns=[
        ('WhitePawn', (i, 1), chess_promotion) for i in range(8)
    ],

    black_monarchs=[('King', (4, 7))],
    black_pieces=[
        (chess_pieces[i], (i, 7)) if i < 4 else (chess_pieces[6-i], (i+1, 7)) for i in range(7)
    ],
    black_pawns=[
        ('BlackPawn', (i, 6), chess_promotion) for i in range(8)
    ]
)


# a shatranj set
shatranj_pieces = ['Rook', 'Knight', 'Alfil', 'Ferz']
shatranj_promotion = ['Ferz']
Shatranj = Set(
    dimensions=[8, 8],

    white_monarchs=[('ShatranjKing', (4, 0))],
    white_pieces=[
        (shatranj_pieces[i], (i, 0)) if i < 4 else (shatranj_pieces[6-i], (i+1, 0))  for i in range(7) 
    ],
    white_pawns=[
        ('ShatranjWhitePawn', (i, 1), shatranj_promotion) for i in range(8)
    ],

    black_monarchs=[('ShatranjKing', (4, 7))],
    black_pieces=[
        (shatranj_pieces[i], (i, 7)) if i < 4 else (shatranj_pieces[7-i], (i+1, 7)) for i in range(7)
    ],
    black_pawns=[
        ('ShatranjBlackPawn', (i, 6), shatranj_promotion) for i in range(8)
    ]
)


# a wildebeest set
wildebeest_pieces = ['Rook', 'Knight', 'Camel', 'Camel', 'Wildebeest', 'Queen', 'Bishop', 'Bishop', 'Knight', 'Rook']
wildebeest_promotion = ['Queen', 'Wildebeest']
Wildebeest = Set(
    dimensions = [11, 10],
    
    white_monarchs=[('WildebeestKing', (5, 0))],
    white_pieces=[
        (wildebeest_pieces[i], (i, 0) if i < 5 else (i+1, 0)) for i in range(10) 
    ],
    white_pawns=[
        ('WhitePawn', (i, 1), wildebeest_promotion) for i in range(11)
    ],

    black_monarchs=[('WildebeestKing', (5, 9))],
    black_pieces=[
        (wildebeest_pieces[i], (i, 9) if i < 5 else (i+1, 9)) for i in range(10) 
    ],
    black_pawns=[
        ('BlackPawn', (i, 8), wildebeest_promotion) for i in range(11)
    ]
)
