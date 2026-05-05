from game import *


class Standard:
    @staticmethod
    def King() -> Figure:
        return Figure('K', 0, discrete = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)])
    
    @staticmethod
    def Queen() -> Figure:
        return Figure('Q', 9, spanning=[(0,1), (1, 0), (1, 1), (1, -1)])
    
    @staticmethod
    def Rook() -> Figure:
        return Figure('R', 5, spanning=[(1, 0), (0, 1)])
    
    @staticmethod
    def Bishop() -> Figure:
        return Figure('B', 3, spanning=[(1, 1), (-1, 1)])
    
    @staticmethod
    def Knight() -> Figure:
        return Figure('N', 3, discrete=[(2, 1), (1, 2), (-1, 2), (-2, 1), (2, -1), (1, -2), (-2, -1), (-1, -2)])
    

    @staticmethod 
    def White() -> Player:
        army = [
            Piece(Standard.Rook(), (0, 0)), Piece(Standard.Rook(), (7, 0)),
            Piece(Standard.Knight(), (1, 0)), Piece(Standard.Knight(), (6, 0)),
            Piece(Standard.Bishop(), (2, 0)), Piece(Standard.Bishop(), (5, 0)),
            Piece(Standard.Queen(), (3, 0)),
        ]

        for i in range(8):
            army.append(Piece(Figure('p', 1, discrete=[(0, 1)], first=[(0, 2)], takes=[(-1, 1), (1, 1)], takes_exclusive=True), (i, 1)))

        return Player(
            general = Piece(Standard.King(), (4, 0)),
            army = army,
            index=0
        )
    
    @staticmethod
    def Black() -> Player:
        army = [
            Piece(Standard.Rook(), (0, 7)), Piece(Standard.Rook(), (7, 7)),
            Piece(Standard.Knight(), (1, 7)), Piece(Standard.Knight(), (6, 7)),
            Piece(Standard.Bishop(), (2, 7)), Piece(Standard.Bishop(), (5, 7)),
            Piece(Standard.Queen(), (3, 7)),
        ]

        for i in range(8):
            army.append(Piece(Figure('p', 1, discrete=[(0, -1)], first=[(0, -2)], takes=[(-1, -1), (1, -1)], takes_exclusive=True), (i, 6)))

        return Player(
            general = Piece(Standard.King(), (4, 7)),
            army = army,
            index=1
        )
    

    @staticmethod
    def Set() -> Game:
        return Game([8, 8], [Standard.White(), Standard.Black()])


    