# Demetre Seturidze
# Chess
# Game

from files.player import * 
from typing import Dict
from itertools import product

class Status:
    ONGOING = 0
    CHECKMATE = 1
    STALEMATE = 2
    PROMOTING = 3

#TODO: sometimes checkmates register erroneously, like when queen should be able to take the attacker
#TODO: add takebacks, show previous positions, etc...
#TODO: make game a separate thing on top of the board. the board should be able to be set up however it be so desired,
# with whichever pieces.
class Game:
    def __init__(
        self,
        dimensions : List[int],
        players : List[Player]
        ):

        self.rank = len(dimensions)
        self.board = np.full(dimensions, -1)
        self.dimensions = dimensions
        self.players = players

        self.basis = np.eye(self.rank)

        # the player whose turn it is
        self.turn = 0
        self.move_num = 0  # the amount of times that every player has made a move (after each player makes one move, we increment)
        
        self.status : int = Status.ONGOING
        
        self.promoting = None # the piece which is currently promoting 

        assert all(player.rank == self.rank for player in players)
        
        self.pieces : Dict[int, Piece] = {}

        i = 0
        for player in players:
            for monarch in player.monarchs:
                self.pieces[i] = (monarch)
                self.board[monarch.position] = i
                i += 1

            for piece in player.army:
                self.pieces[i] = piece
                self.board[piece.position] = i
                i += 1
        
    # returns the entity at the given position
    def at(self, pos : tuple | Vector) -> Piece | None:
        if isinstance(pos, np.ndarray):
            pos = tuple(pos.tolist())

        i = self.board[pos]
        return None if i == -1 else self.pieces[i]
    

    # temporarily moves the given piece to the given position and runs the given function with the given arguments
    def condition(self, piece : Piece, pos : tuple | Vector, func : Callable, *args):
        _cpos = piece.position
        _cvec = piece.vector 

        if isinstance(pos, np.ndarray):
            vec = pos 
            pos = tuple(pos.tolist())
        else:
            pos = pos 
            vec = np.array(pos)

        piece.position = pos
        piece.vector = vec

        _cpiece = self.board[_cpos]
        self.board[_cpos] = -1

        _opiece = self.board[pos]
        if _opiece != -1:
            self.pieces[_opiece].dead = True 
        self.board[pos] = _cpiece

        result = func(*args)

        piece.position = _cpos 
        piece.vector = _cvec 

        self.board[pos] = _opiece
        if _opiece != -1:
            self.pieces[_opiece].dead = False 
        self.board[_cpos] = _cpiece

        return result

    # returns the Move with which the piece sees the given displacement vector,
    # if condition is not None, it is assumed that we are checking the visibility of a piece *after* the condition piece has been moved to the condition square
    def sees(self, piece : Piece, target : Vector) -> Move | None:
        if piece.dead:
            return False 
        
        start = piece.vector

        # check for starting moves.
        if not piece.has_moved:
            for move in piece.figure.first:
                if move.accesses(self, start, target):
                    return move
            if piece.figure.first_exclusive:
                return None
            
        # otherwise, check the remaining moves
        for move in piece.figure.moves:
            if move.accesses(self, start, target):
                return move

    # returns True if the player is in check
    def in_check(self, player : Player) -> bool:   
        if len(player.monarchs) > 1:
            return False
        else:
            target = player.monarchs[0].vector

            for opponent in self.players:
                if opponent is not player:

                    for monarch in opponent.monarchs:
                        if self.sees(monarch, target):
                            return True
                    
                    for piece in opponent.army:
                        if self.sees(piece, target):
                            return True
            
            return False

    # checks if anyone is in check and updates
    # returns True if any new checks are declared
    def update_checks(self) -> bool:
        result = False 

        for player in self.players:
            declared_check = self.in_check(player)

            if declared_check and not player.is_in_check:
                result = True 
            
            player.is_in_check = declared_check 
        
        return result

    # executes a move, returns the nature of the move (move, take, check, etc...)
    # allows us to enforce move rules and game rules at will.
    def move(self, piece : Piece, target : tuple | Vector) -> List[str]:
        assert len(target) == self.rank

        player = piece.player

        
        if self.promoting is not None:
            raise Exception('Promoting piece has not yet been promoted.')
        
        if piece.dead:
            raise Exception('The given piece is dead.')
        
        if not self.in_bounds(target):
            raise Exception('Target square out of bounds.') 

        # if it is not the player's turn, return false
        if player is not self.players[self.turn]:
            raise Exception('Opponent\'s turn.')

        # make sure the player does not walk into check
        if self.condition(piece, target, self.in_check, player):
            raise Exception('Player will be in check.')

        move = self.sees(piece, target)
        
        # check otherwise legality
        if move is None:
            raise Exception('Illegal move.')
        
        player.is_in_check = False

        castle_like = piece is player.monarchs[0] and move.special_exec is not None
        result = ['castle'] if castle_like else ['move']

        target_piece = self.at(target)

        if target_piece is not None: 
            # if the target square is occupied, check that we can capture the piece
            if move.captures and target_piece.player is player:
                raise Exception('Illegal capture.')
            
        if move.execute(self, piece, target):
            result = ['take']
        
        for s in self.pieces.values():
            s.just_first = not s.has_moved 
            s.update_history()

        piece.has_moved = True 

        # we check for the possibility of promotion. 
        index = piece.promotion_axis
        if piece.promotion_list:
            sign = 1 if piece.position[index] - piece.history[0][index] > 0 else -1
            # if we are at the edge of the board in the correct axis, we promote
            if not self.in_bounds(piece.vector + sign * self.basis[index]):
                if len(piece.promotion_list) == 1:
                    piece.figure = piece.promotion_list[0]
                    result.append('promote')

                    # a piece may only promote once
                    piece.promotion_list = [] 
                else:
                    self.promoting = piece
                    self.status = Status.PROMOTING
                    

        check = self.update_checks()
        if check:
            result.append('check')

            if 'move' in result:
                result.remove('move')

        # update turns and moves
        self.turn = (self.turn + 1) % len(self.players)
        if self.turn == 0:
            self.move_num += 1
            
        # if the player is out of legal moves, the game ends
        if not self.has_legal_moves(self.players[self.turn]):
            result.append('end')
            self.status = Status.CHECKMATE if check else Status.STALEMATE

        return result 
    
    def promote(self, figure : Figure) -> List[str]:
        if self.promoting is not None:
            self.promoting.figure = figure
            # we may only promote once
            self.promoting.promotion_list = [] 
            self.promoting = None 
            
            result = ['promote']

            check = self.update_checks()
            if check:
                result.append('check')
            else:
                result.append('move')
            if not self.has_legal_moves(self.players[self.turn]):
                result.append('end')
                self.status = Status.CHECKMATE if check else Status.STALEMATE 
            else:
                self.status = Status.ONGOING

            return result
        
        else:
            raise Exception('No pieces are currently promoting.')

    def in_bounds(self, pos : tuple | Vector):
        pos = np.array(pos)
        return all(pos >= 0) and all(pos < self.board.shape)
    
    # returns None if the given move is legal, otherwise returns an error message
    def _is_illegal(self, piece : Piece, target : Vector) -> str | None:
        player = piece.player 

        # if it is not the player's turn, return false
        if player is not self.players[self.turn]:
            return True

        # make sure the player does not walk into check
        if self.condition(piece, target, self.in_check, player):
            return True
        
        target_piece = self.at(target)
        
        if target_piece is not None: 
            # if the target square is occupied, check that we can capture the piece
            if target_piece.player is player:
                return True 
    
        return False 
    
    # returns True if there remain legal moves for the given piece
    def _piece_has_legal_moves(self, piece : Piece) -> bool:
        if piece.dead:
            return False
        
        for square in piece.available_squares(self):
            if not self._is_illegal(piece, square):
                return True 
    
        return False 
    

    # returns True if there remain legal moves for the player
    def has_legal_moves(self, player : Player) -> bool:
        if len(player.monarchs) > 1:
            return True 
        
        return self._piece_has_legal_moves(player.monarchs[0]) or any(self._piece_has_legal_moves(piece) for piece in player.army)



        

            