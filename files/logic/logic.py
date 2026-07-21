# Demetre Seturidze
# Chess
# Logic

from files.logic.figures import Move, Castle, Vector, Figures
from typing import Dict, Tuple, List, Callable, Optional
import numpy as np, time

from netlib.serialization import Serializable, to_native

# here we rigorously apply 'to_native' hopefully to uproot any 
# serialization errors 

# -- THE PLAYER and THE PIECES -- #

class Player(Serializable):
    def __init__(
        self,
        monarchs : List['Piece'] | 'Piece', # king piece
        army : List['Piece'], 
        index : int,
    ):
        self.index = index

        self.monarchs = [monarchs] if isinstance(monarchs, Piece) else monarchs
        for monarch in self.monarchs:
            monarch.player = self 

        self.army = army
        for piece in army:
            piece.player = self

        self.rank = monarch.figure.dim 

        assert all(piece.figure.dim == self.rank for piece in self.army)

        self.material = sum(piece.figure.value for piece in self.army) # counts raw value for material

        self.is_in_check : bool = False # keeps track if the player is in check

    # serialization
    def to_dict(self) -> dict:
        return {
            'monarchs' : self.monarchs,
            'army' : self.army,
            'index' : to_native(self.index)
        }
    

class Piece(Serializable):
    def __init__(
        self,
        name : str,
        position : tuple,

        promotes : List[str] | None = None, # a list of figures to which a figure may promote upon reaching the other end of the board 
        promotion_axis : int = -1, # the promotion axis

        history : List[tuple] | None = None, # the history of positions this has had
        dead : bool = False,

        has_moved : bool = False,
        just_first : bool = False
    ):
        self.player : Player | None = None 
        self.figure = Figures[name]
        self.name = name

        self.history = history = history or []
        self.update_position(position)

        self.promotes = promotes = promotes or []
        self.promotion_list = [Figures[name] for name in promotes]
        self.promotion_axis = promotion_axis

        self.dead = dead

        self.has_moved = has_moved 
        self.just_first = just_first
    
    # serialization
    def to_dict(self) -> dict:
        return {
            'name' : self.name,
            'position' : self.position,
            
            'promotes' : self.promotes,
            'promotion_axis' : to_native(self.promotion_axis),

            'history' : to_native(self.history[:-1]),
            'dead' : False,

            'has_moved' : False,
            'just_first' : False
        }

    def update_position(self, position : tuple | Vector):
        self.position = tuple(to_native(position))
        if isinstance(position, np.ndarray):
            self.vector = position
        else:
            self.vector = np.array(position)
        
        self.history.append(self.position)
        

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
                yield from move.available_squares(game, self.vector)
            
        if not self.figure.first_exclusive:    
            for move in self.figure.moves:
                yield from move.available_squares(game, self.vector)
                



# -- THE GAME and THE GAME STATUS -- #
# the actual rules and state of the game.

class Status:
    UNBEGUN = -1
    ONGOING = 0
    CHECKMATE = 1
    STALEMATE = 2
    TIMEOUT = 3
    PROMOTING = 4


from dataclasses import dataclass, fields, field

ALPHABET = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']
# an action in a game. includes a displacement (start, end), and a promotion index (if we promote)
@dataclass 
class Action(Serializable):
    displacement : Tuple[Tuple[int, int], Tuple[int, int]] | None = None  
    times : List[float] | None = None 
    start_time : float | None = None 
    end_time : float | None = None 
    promote_to : int = -1 

    def to_dict(self) -> dict:
        result = {}

        for field in fields(self):
            obj = getattr(self, field.name)
            if obj is not None:
                result[field.name] = to_native(obj)

        return result
    
    @classmethod 
    def from_dict(cls, action : dict | None) -> Optional['Action']:
        if action is None: return None 
        displacement = action.pop('displacement')
        return Action(displacement=tuple(tuple(j) for j in displacement), **action)
    
    def __str__(self) -> str:
        moves = [f'{ALPHABET[d[0]]}{d[1]+1}' for d in self.displacement]
        string = '-'.join(moves)
        return string if self.promote_to == -1 else f'{string}P{self.promote_to}'


@dataclass
class Event(Serializable):
    # label is move if this is just a move,
    # reset if reset,
    # quit if quit,
    # promote if promote.
    label : str = 'none'
    index : int = -1
    sounds : List[str] = field(default_factory=list)
    action : Action | None = None 
    text : str | None = None

    def to_dict(self) -> dict:
        return {
            'label' : self.label,
            'index' : self.index,
            'sounds' : self.sounds,
            'action' : self.action,
            'text' : self.text 
        }



#TODO: sometimes checkmates register erroneously, like when queen should be able to take the attacker
#TODO: add takebacks, show previous positions, etc...
Round = List[Action]
class Game(Serializable):
    def __init__(
        self,
        dimensions : List[int],
        players : List[Player],

        history : List[Round] | None = None, # for serialization purposes
        status : int = Status.UNBEGUN,
        times : List[float] | None = None,

        turn_start_time : float | None = None,

        default_time_s : float = 600 # default time 10 min per player

    ):
        history = history or [[]]

        self.rank = len(dimensions)
        self.board = np.full((*dimensions, 2), -1)
        self.dimensions = dimensions
        self.players = players

        self.basis = np.eye(self.rank)
        
        self.status : int = status 
        
        self.promoting = None # the piece which is currently promoting 
        self.delayed_event = None # the event which is delayed by promotion

        assert all(player.rank == self.rank for player in players)
        
        self.pieces : List[Dict[int, 'Piece']] = [{} for _ in players] # indexed according to the index of the corresponding player
        
        if times is None:
            self.times = [default_time_s for _ in players]
        else:
            self.times = times.copy() 

        self.captured_pieces : List[List[Tuple[int, str]]] = [[] for _ in players] 
        # indexed similarly:
        # captured_pieces[i] is a list of tuples (player_index, piece_name) corresponding to the pieces that player i has captured.
        
        i = 0
        for j in range(len(players)):
            player = players[j]
            pieces = self.pieces[j]

            for monarch in player.monarchs:
                pieces[i] = monarch
                square = self.board[monarch.position]

                square[0] = j 
                square[1] = i 
                i += 1

            for piece in player.army:
                pieces[i] = piece
                square = self.board[piece.position]

                square[0] = j 
                square[1] = i 
                i += 1
            
            i=0
        

        # HISTORY/LOADING

        self.move_num = len(history)-1 # the amount of times that every player has made a move (after each player makes one move, we increment)
        self.turn = len(history[-1]) % len(self.players) # the player whose turn it is

        self.turn_start_time = turn_start_time

        self.history : List[Round] = history # registers the history


    # returns the entity at the given position
    def at(self, pos : tuple | Vector) -> Piece | None:
        if not self.in_bounds(pos):
            return None 
        pos = tuple(pos)
        pos = (int(pos[0]), int(pos[1]))

        i, j = tuple(self.board[pos])
        return None if i == -1 else self.pieces[i][j]

    def set_to(self, pos : tuple | Vector, player_index : int, piece_index : int):
        square = self.board[tuple(pos)]
        square[0] = player_index
        square[1] = piece_index
    

    # temporarily moves the given piece to the given position and runs the given function with the given arguments
    def condition(self, piece : Piece, pos : tuple | Vector, func : Callable, *args):
        _cpos = piece.position

        piece.update_position(pos)
        pos = piece.position

        _cplayer, _cpiece = to_native(self.board[_cpos]) # current piece
        self.set_to(_cpos, -1, -1) # removes the current piece from the current position

        _oplayer, _opiece = to_native(self.board[pos]) # original piece 

        if _opiece != -1:
            self.pieces[_oplayer][_opiece].dead = True 

        self.set_to(pos, _cplayer, _cpiece)

        result = func(*args)

        piece.update_position(_cpos)

        self.set_to(pos, _oplayer, _opiece)
 
        if _opiece != -1:
            self.pieces[_oplayer][_opiece].dead = False 
 
        self.set_to(_cpos, _cplayer, _cpiece)

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


    # allows us to take a piece that is not at the end position of the move.
    # also allows us to explicitly not capture anything (should be used back-end strictly, in order to avoid inconsistency)
    def generalized_execute(self, piece : Piece, end_pos : tuple | Vector, capture_displacement : Vector | None = None) -> bool:
        kill_target = end_pos + capture_displacement if capture_displacement is not None else end_pos

        target_piece = self.at(kill_target)
        result = target_piece is not None
        if result:
            i, j = tuple(self.board[target_piece.position])

            self.set_to(target_piece.position, -1, -1)
            target_piece.die()
            self.pieces[i].pop(j)

            capturing_player = piece.player.index
            self.captured_pieces[capturing_player].append((i, target_piece.figure.name))

        self.set_to(end_pos, *tuple(self.board[piece.position]))
        self.set_to(piece.position, -1, -1)

        piece.update_position(end_pos) 
        
        return result

    # executes this move
    def _execute(self, move : Move, piece : Piece, target : Vector):
        if move.special_execute:
            return move.special_execute(self, piece, target)
        else:
            return self.generalized_execute(piece, target, move.capture_displacement)

    # increments the turn and updates the game history
    def _next_turn(self):
        self.turn = (self.turn + 1) % len(self.players)
        if self.turn == 0:
            self.move_num += 1
            self.history.append([])

    # executes a move, returns the nature of the move (move, take, check, etc...)
    # allows us to enforce move rules and game rules at will.
    def move(self, piece : Piece, target : tuple | Vector, update_time : bool = True) -> Event:
        assert len(target) == self.rank

        target = tuple(target)
        target = (
            int(target[0]),
            int(target[1])
        )

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

        sounds = ['castle'] if isinstance(move, Castle) else ['move']

        target_piece = self.at(target)

        if target_piece is not None: 
            # if the target square is occupied, check that we can capture the piece
            if move.captures and target_piece.player is player:
                raise Exception('Illegal capture.')
        
        # keeps track of start and end positions
        action = Action(displacement=(piece.position, tuple(target)))

        if self._execute(move, piece, target):
            sounds = ['take']
        
        for player_army in self.pieces:
            for s in player_army.values():
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
                    sounds.append('promote')

                    # a piece may only promote once
                    piece.promotion_list = [] 
                else:
                    self.promoting = piece
                    self.status = Status.PROMOTING

        event = Event(label='action', index=self.turn, action=action, sounds=sounds)

        # update turns and moves
        if self.status != Status.PROMOTING:
            return self._post_move_update(event, update_time=update_time)
        else:
            self.delayed_event = event
            return Event()
    
    def register_action(self, action : Action):
        if self.status == Status.UNBEGUN:
            self.status = Status.ONGOING
            self.turn_start_time = time.time()

        s, e = action.displacement
        self.move(self.at(s), e, update_time=False)

        if action.promote_to >= 0:
            self.promote(action.promote_to, update_time=False)
        
        self.times = action.times.copy()
        self.turn_start_time = action.end_time
        
    # update process after a move has been completed.
    # checks for checks, registers the necessary sounds, updates history
    def _post_move_update(self, event : Event, update_time=True):
        if update_time:
            if self.status == Status.UNBEGUN:
                self.status = Status.ONGOING
                self.turn_start_time = turn_end_time = time.time()
            elif self.status == Status.ONGOING and update_time:
                turn_end_time = time.time()
                time_dif = turn_end_time - self.turn_start_time
                self.times[self.turn] -= time_dif
            
            event.action.times = self.times.copy()
            event.action.start_time = self.turn_start_time
            event.action.end_time = turn_end_time
            
            self.turn_start_time = turn_end_time    
        
        self._next_turn()

        check = self.update_checks()
        if check:
            event.sounds.append('check')

            if 'move' in event.sounds:
                event.sounds.remove('move')
        
        # if the player is out of legal moves, the game ends
        if not self.has_legal_moves(self.players[self.turn]):
            event.sounds.append('end')
            self.status = Status.CHECKMATE if check else Status.STALEMATE

        # registers the move in the game history
        self.history[-1].append(event.action)
        return event

    
    def promote(self, promotion_index : int, update_time : bool = True) -> Event:
        if self.promoting is not None:
            self.promoting.figure = self.promoting.promotion_list[promotion_index]
            # we may only promote once
            self.promoting.promotion_list = [] 
            self.promoting = None 
            
            self.status = Status.ONGOING 


            event = self._post_move_update(self.delayed_event, update_time=update_time)
            self.delayed_event = None 
            
            event.sounds.append('promote')
            event.action.promote_to = promotion_index
            return event
        else:
            raise Exception('No pieces are currently promoting.')
    
    def in_bounds(self, pos : tuple | Vector):
        pos = np.array(pos)
        return all(pos >= 0) and all(pos < self.board.shape[:self.rank])
    
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
        
        king_can_move = self._piece_has_legal_moves(player.monarchs[0])
        anything_else_can_move = any(self._piece_has_legal_moves(piece) for piece in player.army)

        return king_can_move or anything_else_can_move


    # serialization
    def to_dict(self) -> dict:
        return {
            'players' : self.players,
            'dimensions' : to_native(self.dimensions),

            'history' : self.history,
            'status' : to_native(self.status),
            'times' : to_native(self.times),
            'turn_start_time' : to_native(self.turn_start_time),

            'captures' : to_native(self.captured_pieces)
        }
    
    @classmethod
    def from_dict(cls, dct) -> 'Game':
        captured_pieces = dct.pop('captures')
        game = cls(**dct)
        game.captured_pieces = captured_pieces
        return game 
    
    
    def print_history(self):
        i = 1
        for round in self.history:
            if len(round) != 0:
                round_strs = ' :: '.join([str(action) for action in round])
                print(f'{i}.\t{round_strs}')
                i+=1
            