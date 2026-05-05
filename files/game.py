# Demetre Seturidze
# Chess
# Pieces

from files.player import * 

#TODO: add castling, promotion, en passant (i.e. special visibility and special moves)
#TODO: add restartability, move history, takebacks, show previous positions, etc...
#TODO: i was able to move my king into a check by a pawn. take care of this.
class Game:
    def __init__(
        self,
        dimensions : List[int],
        players : List[Player]
        ):

        self.rank = len(dimensions)
        self.board = np.full(dimensions, -1)
        self.players = players

        # the player whose turn it is
        self.turn = 0
        self.move_num = 0  # the amount of times that every player has made a move (after each player makes one move, we increment)

        assert all(player.rank == self.rank for player in players)
        
        self.entities : List[Piece] = []

        self.generals : List[Piece] = []

        for player in players:
            self.entities.append(player.general)
            self.generals.append(player.general)
            self.board[player.general.position] = len(self.entities) - 1

            for piece in player.army:
                self.entities.append(piece)
                self.board[piece.position] = len(self.entities) - 1


    # returns the entity at the given position
    def at(self, pos : tuple | Vector) -> Piece | None:
        if isinstance(pos, np.ndarray):
            pos = tuple(pos.tolist())

        i = self.board[pos]
        return None if i == -1 else self.entities[i]
    
    # returns True if the path given by the displacement (disp) from the current position (vec) using the spanning vector (move)
    # is blocked by some piece
    #
    # if inclusive is false, we do not include the final square
    def is_blocked(self, vec : Vector, move : Vector, disp : Vector, inclusive : bool = False):
        # find the set of positions between current and target, 
        # make sure nothing is in the way
        k = None
        for i in range(len(move)):
            if move[i] != 0:
                k = disp[i] // move[i]
                break
        
        sign = 1 if k > 0 else -1
        k = sign * k

        move = sign * move 

        for _ in range(1, k+1 if inclusive else k):
            vec = vec + move 

            if not self.in_bounds(vec):
                break
            
            pos = tuple(vec.tolist())
            if self.board[pos] != -1:
                return True
        
        return False 

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
        self.entities[_opiece].dead = True 
        self.board[pos] = _cpiece

        result = func(*args)

        piece.position = _cpos 
        piece.vector = _cvec 

        self.board[pos] = _opiece
        self.entities[_opiece].dead = False 
        self.board[_cpos] = _cpiece

        return result

    # returns True if the piece sees the given displacement vector, barring captures,
    # if condition is not None, it is assumed that we are checking the visibility of a piece *after* the condition piece has been moved to the condition square
    def sees(self, piece : Piece, disp : Vector, inclusive : bool = False) -> bool:
        if piece.dead:
            return False 
        
        # check for starting moves.
        if not piece.has_moved:
            if any(all(disp == move) for move in piece.figure.first):
                return True
            elif piece.figure.first_exclusive:
                return False

        for move in piece.figure.spanning:
            # find spanning move that corresponds to the given target square
            if consistent(move, disp):
                # ensure nothing blocks
                return not self.is_blocked(vec=piece.vector, move=move, disp=disp, inclusive=inclusive)
            
        # otherwise, check the discrete moves

        # NOTE: it is here assumed that discrete moves cannot be blocked. (like horse).
        #       alter if need be.
        return any(all(disp == move) for move in piece.figure.discrete) 


    # returns True if the given piece attacks the target square
    # if condition is not None, same applies as in sees()
    def attacks(self, piece : Piece, target : tuple | Vector | Piece) -> bool:
        if piece.dead:
            return False 
        
        if isinstance(target, Piece):
            target = target.vector

        disp = piece.displacement(target)

        if piece.figure.takes:
            if any(all(disp == move) for move in piece.figure.takes):
                return True 
            elif piece.figure.takes_exclusive:
                return False
        
        return self.sees(piece, disp)

    # returns True if the given player attacks the target square,
    # see above for the condition parameter
    def player_attacks(self, player : Player, target : tuple | Vector | Piece) -> bool:
        return self.attacks(player.general, target) or any(self.attacks(piece, target) for piece in player.army)

    # returns True if any player other than the given one attacks the target square
    # see above for the condition parameter
    #
    # TODO: what if a piece is pinned? take into account
    def under_attack(self, player : Player, target : tuple | Vector | Piece) -> bool:
        return any(opponent is not player and self.player_attacks(opponent, target) for opponent in self.players)
    
    # returns True if the given castle is valid 
    # see above for the condition parameter
    def can_castle(self, piece : Piece):
        if piece.has_moved or piece.player.general.has_moved:
            return False 

        #TODO: write this        
        pass
                

    # returns a list of all pieces that the given player has that attack the target square
    # see above for the condition parameter
    def attackers(self, player : Player, target : tuple | Vector) -> bool:
        result = []
        
        if self.attacks(player.general, target):
            result.append(player.general)
        
        for piece in player.army:
            if self.attacks(piece, target):
                result.append(piece)

        return result 

    # checks if anyone is in check and updates
    # returns True if any new checks are declared
    def update_checks(self) -> bool:
        result = False 

        for player in self.players:
            declared_check = self.under_attack(player, player.general)

            if declared_check and not player.in_check:
                result = True 
            
            player.in_check = declared_check 
        
        return result


    # returns None if the given move is legal, otherwise returns an error message
    def illegality(self, piece : Piece, target : tuple | Vector) -> str | None:
        assert len(target) == self.rank

        if piece.dead:
            return 'The given piece is dead.'

        player = piece.player 

        # if it is not the player's turn, return false
        if player is not self.players[self.turn]:
            return 'Opponent\'s turn.' 

        # make sure the player does not walk into check
        if self.condition(piece, target, self.under_attack, player, player.general):
            return 'Player will be in check.'

        target_piece = self.at(target)

        if target_piece is not None: 
            # if the target square is occupied, check that we can capture the piece
            if target_piece.player is player:
                return 'Cannot capture own piece.'
            elif self.attacks(piece, target):
                return None 
            else:
                return 'Illegal capture.'
        
        # check otherwise legality
        if not self.sees(piece, piece.displacement(target), inclusive=True):
            return 'Illegal move.'
        
        return None 
    
    # executes a move, returns the nature of the move (move, take, check, etc...)
    def move(self, piece : Piece, target : tuple | Vector) -> str:
        player = piece.player

        illegality = self.illegality(piece, target)
        if illegality is not None:
            raise Exception(illegality)
        
        player.in_check = False 
        result = 'move'

        target_piece = self.at(target)
        if target_piece is not None:
            target_piece.die()
            result = 'take'

        self.board[target] = self.board[piece.position]
        self.board[piece.position] = -1 

        if isinstance(target, np.ndarray):
            piece.position = tuple(target.tolist())
            piece.vector = target
        else:
            piece.position = target
            piece.vector = np.array(target)
        

        piece.just_first = not piece.has_moved 
        piece.has_moved = True 

        if self.update_checks():
            result = 'check'

        # update turns and moves
        self.turn = (self.turn + 1) % len(self.players)
        if self.turn == 0:
            self.move_num += 1

        current_player = self.players[self.turn]
        if not self.has_legal_moves(self.players[self.turn]):
            if current_player.in_check:
                result = 'checkmate'  
            else:
                result = 'stalemate' 

        return result 
            

    def in_bounds(self, pos : tuple | Vector):
        pos = np.array(pos)
        return all(pos >= 0) and all(pos < self.board.shape)
    
    # returns True if there remain legal moves for the given piece
    def _piece_has_legal_moves(self, piece : Piece) -> bool:
        if not piece.has_moved:
            for move in piece.figure.first:
                vec = piece.vector + move

                if not self.in_bounds(vec):
                    continue

                if self.illegality(piece, vec) is None:
                    return True
            
            if piece.figure.first_exclusive:
                return False 
        
        for move in piece.figure.spanning:
            vec = piece.vector + move
            while self.in_bounds(vec):
                empty = self.at(vec) is None

                if (empty or not piece.figure.takes_exclusive) and self.illegality(piece, vec) is None:
                    return True
                
                if not empty:
                    break

                vec = vec + move 
        
        for move in piece.figure.discrete:
            vec = piece.vector + move 

            if not self.in_bounds(vec):
                continue

            if (self.at(vec) is None or not piece.figure.takes_exclusive) and self.illegality(piece, vec) is None:
                return True 
        

        for move in piece.figure.takes:
            vec = piece.vector + move 

            if not self.in_bounds(vec):
                continue

            if self.at(vec) is not None and self.illegality(piece, vec) is None:
                return True 
        
        return False 
    
    # returns True if there remain legal moves for the player
    def has_legal_moves(self, player : Player) -> bool:
        if self._piece_has_legal_moves(player.general):
            return True 
        
        return any(self._piece_has_legal_moves(piece) for piece in player.army)


    # TODO: write a castling function and validity checks for it 


        

            