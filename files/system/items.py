# Demetre Seturidze
# Chess
# Items


from netlib.serialization import Serializable
from netlib.graph import Node, Edge

from dataclasses import dataclass, field
import time

from random import shuffle
from files.engine import EngineResponse, EngineRequest, EngineEvent, Engine, EngineError

@dataclass
class Text(Serializable):
    index : int
    content : str 

    def to_dict(self):
        return {
            'index' : self.index,
            'content' : self.content 
        }


@dataclass
class Auth(Serializable):
    username : str 
    password : str 
    is_new : bool = False

    def to_dict(self):
        return {
            'username' : self.username,
            'password' : self.password,
            'is_new' : self.is_new
        }

@dataclass
class Request(Serializable):
    label : str
    content : str | None = None

    def to_dict(self):
        return {
            'label' : self.label,
            'content' : self.content 
        }

@dataclass
class Challenge(Serializable):
    sender : str
    receiver : str
    game_set : str
    timer : float 
    game_id : str | None = None

    def __post_init__(self):
        if self.game_id is None:
            self.game_id = f'{time.time()}::{self.sender}//{self.receiver}'

    def to_dict(self):
        return {
            'sender' : self.sender,
            'receiver' : self.receiver,
            'game_set' : self.game_set,
            'timer' : self.timer,
            'game_id' : self.game_id
        }

@dataclass
class Response(Serializable):
    label : str
    content : str | None = None

    def to_dict(self):
        return {
            'label' : self.label,
            'content' : self.content 
        }

@dataclass
class Error(Serializable):
    label : str
    content : str | None = None

    def to_dict(self):
        return {
            'label' : self.label,
            'content' : self.content
        }

    

@dataclass
class Layout(Serializable):
    players : tuple[str, str]
    board_str : str
    game_id : str | None = None

    def to_dict(self):
        return {
            'players' : self.players,
            'board_str' : self.board_str,
            'game_id' : self.game_id
        }

    @classmethod
    def from_dict(self, dct : dict):
        return Layout(
            players=tuple(dct['players']),
            board_str = dct['board_str'],
            game_id = dct.get('game_id', None)
        )

@dataclass
class SessionLayout(Serializable):
    layout : Layout
    layout_history : list[Layout]
    chat : list[Text]

    def to_dict(self):
        return {
            'layout' : self.layout,
            'layout_history' : self.layout_history,
            'chat' : self.chat
        }

@dataclass
class UserLayout(Serializable):
    username : str 

    def to_dict(self):
        return {
            'username' : self.username
        }



@dataclass
class Instance(Serializable):
    players : tuple[str, str]
    engine : Engine
    open_time : float
    history : list[EngineEvent] = field(default_factory=list)

    def to_dict(self):
        return {
            'players' : self.players,
            'engine' : self.engine.embed(),
            'open_time' : self.open_time,
            'history' : self.history
        }

    def to_layout(self):
        return Layout(
            players = self.players,
            board_str=self.engine.layout()
        )

    @classmethod
    def from_dict(cls, dct):
        return cls(
            players = tuple(dct['players']),
            engine=Engine.disembed(dct['engine']),
            open_time=dct['open_time'],
            history=dct['history']
        )


SystemResponse = Text | EngineResponse | Response | EngineEvent | EngineError | Layout | UserLayout | SessionLayout | Error  
SystemRequest = Text | EngineRequest | Request | Auth | Error 

@dataclass
class Session(Serializable):
    set_name : str 
    timer : float 

    players : tuple[str, str]

    instance : Instance | None = None
    layout : Layout | None = None 

    history : list[dict] = field(default_factory=list)
    layout_history : list[Layout] = field(default_factory=list)

    chat : list[Text] = field(default_factory=list)

    
    def to_dict(self):
        return {
            'set_name' : self.set_name,
            'timer' : self.timer,
            'players' : self.players,
            'instance' : self.instance,
            'layout' : self.layout,
            'history' : self.history,
            'layout_history' : self.layout_history,
            'chat' : self.chat
        }
    
    def to_layout(self):
        return SessionLayout(
            self.layout, self.layout_history, self.chat
        )


    def begin(self, randomize : bool = True, save_current : bool = True) -> Layout:
        if save_current and self.instance is not None:
            self.history.append(self.instance.to_dict())
            self.layout_history.append(self.instance.to_layout())

        pl = self.players.copy()

        if randomize:
            shuffle(pl)

        self.instance = Instance(
            players=pl,
            engine = Engine.construct(self.set_name, self.timer),
            open_time = time.time()
        )

        self.layout = self.instance.to_layout()

        return self.layout


    def look(self) -> str:
        return str(self.instance.engine)


    def process(self, msg : SystemRequest) -> SystemResponse:
        try:
            if isinstance(msg, Text):
                self.chat.append(msg)
                return msg

            elif isinstance(msg, EngineRequest):
                if msg.label == "times":
                    return self.instance.engine.times()
                else:
                    return self.instance.engine.process(msg)

            elif isinstance(msg, Request):
                if msg.label == "reset":
                    if self.instance.engine.is_on():
                        return Error("ongoing", "cannot reset while game is ongoing.")
                    else:
                        return self.begin(randomize=False)

                else:
                    return Error("request", "invalid request.")

            else:
                return Error("type", f"invalid message type {msg.__class__.__name__}.")


        except Exception as e:
            return Error(e.__class__.__name__, str(e))


class User(Node):
    def __init__(self, username : str, password : str):
        super().__init__(username)
        self.password = password
        self.connection = None

    def to_layout(self):
        return UserLayout(self.idstr)
    

    def to_dict(self):
        return {
            'username' : self.idstr,
            'password' : self.password
        }

class Relation(Edge):
    def __init__(self, usernames : tuple[str, str], current_session : Session | None = None, sessions : list[Session] | None = None, buffers : dict[str, list[str]] | None = None):
        super().__init__(usernames)

        self.current_session = current_session 
        self.is_new = True

        self.sessions = sessions or []

        self.connections = {
            usernames[0] : None,
            usernames[1] : None
        }


    def _save(self):
        if self.current_session is not None and self.is_new:
            self.sessions.append(self.current_session)


    async def send_to_both(self, msg : str):
        for c in self.connections.values():
            await c.send(msg)


    def enter(self, session_index : int, save_current : bool = True) -> SessionLayout:
        if save_current:
            self._save()

        self.current_session = self.sessions[session_index]
        self.is_new = False
        return self.current_session.to_layout()

        

    def make(self, set_name : str, timer : float, save_current : bool = True) -> SessionLayout:
        if save_current:
            self._save()

        self.current_session = Session(set_name, timer, self.ids)
        layout = self.current_session.begin()
        self.is_new = True
        return layout


    def exit(self, save_current : bool = True) -> Response:
        if save_current:
            self._save()

        self.current_session = None
        return Response("exit")
    

    def to_dict(self):
        return {
            'usernames' : self.ids,
            'current_session' : self.current_session,
            'sessions' : self.sessions
        }


    

    