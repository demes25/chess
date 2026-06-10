# Demetre Seturidze
# Chess
# Boards

from typing import Type, Dict
from files.logic.moves import Vector, Move, Discrete, Spanning, Leap, Figure
import files.logic.moves as _moves
from files.logic.game import Game, Piece, Player

import numpy as np
from abc import ABC, abstractmethod

# TODO: Make sets instantiable instead of fixed classes

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
    
    Castle = _moves.Castle
    EnPassant = _moves.EnPassant

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

class Set(ABC):
    @staticmethod
    @abstractmethod
    # we create the standard set of pieces given a color forward direction 
    def Figures(forward : int) -> Dict[str, Figure]: 
        pass

    @classmethod 
    @abstractmethod
    def new_game(cls) -> Game:
        pass


# here we store moves and figures for Standard Chess.
# we also have a "constructor" (new_game) which gives us the full game
class Chess(Set): 
    dimensions = [8, 8]

    @staticmethod
    # we create the standard set of pieces given a color forward direction 
    def Figures(forward : int) -> Dict[str, Figure]: 
        return {
            'K' : Figure(
                name = 'King', 
                value = 0, 
                moves = [
                    Moves.Perimeter()
                ],
                first = [
                    Moves.Castle(n=2, width=8, restrict=False)
                ]
            ),

            'Q' : Figure(
                name = 'Queen', 
                value = 9, 
                moves = [
                    Moves.OrthogonalSpan(), Moves.DiagonalSpan()
                ]
            ),

            'R' : Figure(
                name = 'Rook',
                value = 5,
                moves = [
                    Moves.OrthogonalSpan()
                ]
            ),

            'B' : Figure(
                name = 'Bishop',
                value = 3,
                moves = [
                    Moves.DiagonalSpan()
                ]
            ),

            'N' : Figure(
                name = 'Knight',
                value = 3,
                moves = [
                    Moves.KnightLeap()
                ]
            ),

            'p' : Figure(
                name = 'Pawn',
                value = 1,
                moves = [
                    Moves.PawnPush(forward), Moves.PawnTake(forward), Moves.EnPassant(forward)
                ],
                first = [
                    Moves.PawnJump(forward)
                ]
            )
        }

    @classmethod
    def new_game(cls) -> Game:
        white_figures = cls.Figures(1)
        white_army = [
            Piece(white_figures['R'], (0, 0)),
            Piece(white_figures['N'], (1, 0)),
            Piece(white_figures['B'], (2, 0)),
            Piece(white_figures['Q'], (3, 0)),
            Piece(white_figures['B'], (5, 0)),
            Piece(white_figures['N'], (6, 0)),
            Piece(white_figures['R'], (7, 0))
        ]

        promotes = promotes=[white_figures['Q'], white_figures['R'], white_figures['N'], white_figures['B']]
        for i in range(8):
            white_army.append(
                Piece(
                    white_figures['p'], (i, 1), 
                    promotes=promotes
                )
            )
        
        black_figures = cls.Figures(-1)
        black_army = [
            Piece(black_figures['R'], (0, 7)),
            Piece(black_figures['N'], (1, 7)),
            Piece(black_figures['B'], (2, 7)),
            Piece(black_figures['Q'], (3, 7)),
            Piece(black_figures['B'], (5, 7)),
            Piece(black_figures['N'], (6, 7)),
            Piece(black_figures['R'], (7, 7))
        ]
        
        promotes = [black_figures['Q'], black_figures['R'], black_figures['N'], black_figures['B']]
        for i in range(8):
            black_army.append(
                Piece(
                    black_figures['p'], (i, 6), 
                    promotes=promotes
                )
            )
        
        white = Player(
            monarchs = Piece(white_figures['K'], (4, 0)),
            army = white_army,
            index = 0
        )

        black = Player(
            monarchs = Piece(black_figures['K'], (4, 7)),
            army = black_army,
            index = 1
        )

        return Game(cls.dimensions, [white, black])


class Shatranj(Set):
    dimensions = [8, 8]

    @staticmethod 
    def Figures(forward : int) -> Dict[str, Figure]:
        return{
            'K' : Figure(
                name = 'King', 
                value = 0, 
                moves = [
                    Moves.Perimeter()
                ]
            ),

            'F' : Figure(
                name = 'Ferz', 
                value = 2, 
                moves = [
                    Moves.DiagonalStep()
                ]
            ),

            'R' : Figure(
                name = 'Rook',
                value = 5,
                moves = [
                    Moves.OrthogonalSpan()
                ]
            ),

            'A' : Figure(
                name = 'Alfil',
                value = 2,
                moves = [
                    Moves.AlfilLeap()
                ]
            ),

            'N' : Figure(
                name = 'Knight',
                value = 3,
                moves = [
                    Moves.KnightLeap()
                ]
            ),

            'p' : Figure(
                name = 'Pawn',
                value = 1,
                moves = [
                    Moves.PawnPush(forward), Moves.PawnTake(forward)
                ]
            )
        }
    
    @classmethod
    def new_game(cls) -> Game:
        white_figures = cls.Figures(1)
        white_army = [
            Piece(white_figures['R'], (0, 0)),
            Piece(white_figures['N'], (1, 0)),
            Piece(white_figures['A'], (2, 0)),
            Piece(white_figures['F'], (3, 0)),
            Piece(white_figures['A'], (5, 0)),
            Piece(white_figures['N'], (6, 0)),
            Piece(white_figures['R'], (7, 0))
        ]

        for i in range(8):
            white_army.append(
                Piece(
                    white_figures['p'], (i, 1), 
                    promotes=[white_figures['F']]
                )
            )
        
        black_figures = cls.Figures(-1)
        black_army = [
            Piece(black_figures['R'], (0, 7)),
            Piece(black_figures['N'], (1, 7)),
            Piece(black_figures['A'], (2, 7)),
            Piece(black_figures['F'], (3, 7)),
            Piece(black_figures['A'], (5, 7)),
            Piece(black_figures['N'], (6, 7)),
            Piece(black_figures['R'], (7, 7))
        ]
        
        for i in range(8):
            black_army.append(
                Piece(
                    black_figures['p'], (i, 6), 
                    promotes=[black_figures['F']] # TODO: must generalize promotion
                )
            )
        
        white = Player(
            monarchs = Piece(white_figures['K'], (4, 0)),
            army = white_army,
            index = 0
        )

        black = Player(
            monarchs = Piece(black_figures['K'], (4, 7)),
            army = black_army,
            index = 1
        )

        return Game(cls.dimensions, [white, black])


class Wildebeest(Set):
    dimensions = [11, 10]

    @staticmethod
    # we create the standard set of pieces given a color forward direction 
    def Figures(forward : int) -> Dict[str, Figure]: 
        return {
            'K' : Figure(
                name = 'King', 
                value = 0, 
                moves = [
                    Moves.Perimeter()
                ],
                first = [
                    Moves.Castle(n=2, width=11, restrict=True),
                    Moves.Castle(n=3, width=11, restrict=True),
                    Moves.Castle(n=4, width=11, restrict=True)
                ]
            ),

            'Q' : Figure(
                name = 'Queen', 
                value = 9, 
                moves = [
                    Moves.OrthogonalSpan(), Moves.DiagonalSpan()
                ]
            ),

            'R' : Figure(
                name = 'Rook',
                value = 5,
                moves = [
                    Moves.OrthogonalSpan()
                ]
            ),

            'B' : Figure(
                name = 'Bishop',
                value = 3,
                moves = [
                    Moves.DiagonalSpan()
                ]
            ),

            'W' : Figure(
                name = 'Wildebeest',
                value = 5,
                moves=[Moves.KnightLeap(), Moves.CamelLeap()]
            ),

            'C' : Figure(
                name = 'Camel',
                value = 3,
                moves=[Moves.CamelLeap()]
            ),

            'N' : Figure(
                name = 'Knight',
                value = 3,
                moves = [
                    Moves.KnightLeap()
                ]
            ),

            'p' : Figure(
                name = 'Pawn',
                value = 1,
                moves = [
                    Moves.PawnPush(forward), Moves.PawnTake(forward), #Moves.EnPassant(forward)
                ],
                first = [
                    Moves.PawnJump(forward)
                ]
            )
        }

    @classmethod
    def new_game(cls):
        white_figures = cls.Figures(1)
        white_army = [
            Piece(white_figures['R'], (0, 0)),
            Piece(white_figures['N'], (1, 0)),
            Piece(white_figures['C'], (2, 0)),
            Piece(white_figures['C'], (3, 0)),
            Piece(white_figures['W'], (4, 0)),
            Piece(white_figures['Q'], (6, 0)),
            Piece(white_figures['B'], (7, 0)),
            Piece(white_figures['B'], (8, 0)),
            Piece(white_figures['N'], (9, 0)),
            Piece(white_figures['R'], (10, 0))
        ]

        for i in range(11):
            white_army.append(
                Piece(
                    white_figures['p'], (i, 1), 
                    promotes=[white_figures['Q'], white_figures['W']]
                )
            )
        
        black_figures = cls.Figures(-1)
        black_army = [
            Piece(black_figures['R'], (0, 9)),
            Piece(black_figures['N'], (1, 9)),
            Piece(black_figures['C'], (2, 9)),
            Piece(black_figures['C'], (3, 9)),
            Piece(black_figures['W'], (4, 9)),
            Piece(black_figures['Q'], (6, 9)),
            Piece(black_figures['B'], (7, 9)),
            Piece(black_figures['B'], (8, 9)),
            Piece(black_figures['N'], (9, 9)),
            Piece(black_figures['R'], (10, 9))
        ]

        for i in range(11):
            black_army.append(
                Piece(
                    black_figures['p'], (i, 8), 
                    promotes=[black_figures['Q'], black_figures['W']]
                )
            )
        
        white = Player(
            monarchs = Piece(white_figures['K'], (5, 0)),
            army = white_army,
            index = 0
        )

        black = Player(
            monarchs = Piece(black_figures['K'], (5, 9)),
            army = black_army,
            index = 1
        )

        return Game(cls.dimensions, [white, black])
    

sets : Dict[str, Type[Set]] = {
    'chess' : Chess,
    'shatranj' : Shatranj,
    'wildebeest' : Wildebeest
}