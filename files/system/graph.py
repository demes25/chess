# Demetre Seturidze
# Chess
# Graph


from netlib.serialization import Serializable
from dataclasses import dataclass, field
import time

from files.engine import Response, Request, Event, Engine

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
class Chat(Serializable):
    content : list[Text]

    def to_dict(self):
        return {
            'content' : self.content
        }

SystemMessage = Text | Chat | Response | Event
UserMessage = Text | Request



@dataclass
class Instance(Serializable):
    engine : Engine
    open_time : float
    history : list[Event] = field(default_factory=list)

    def to_dict(self):
        return {
            'engine' : self.engine.embed(),
            'open_time' : self.open_time,
            'history' : self.history
        }

    @classmethod
    def from_dict(cls, dct):
        return cls(
            engine=Engine.disembed(dct['engine']),
            open_time=dct['open_time'],
            history=dct['history']
        )



@dataclass
class Processor(Serializable):
    set_name : str 
    timer : float 

    instance : Instance | None = None
    history : list[dict] = field(default_factory=list)

    chat : list[Text] = field(default_factory=list)

    
    def to_dict(self):
        return {
            'set_name' : self.set_name,
            'timer' : self.timer,
            'instance' : self.instance,
            'history' : self.history,
            'chat' : self.chat,
        }


    def begin(self, save : bool = True) -> Response:
        if save and self.instance is not None:
            self.history.append(self.instance.to_dict())

        self.instance = Instance(
            engine = Engine.construct(self.set_name, self.timer),
            open_time = time.time()
        )

        return Response.construct("layout", self.instance.engine.layout())


    def look(self) -> str:
        return str(self.instance.engine)


    def process(self, msg : UserMessage) -> SystemMessage:
        try:
            if isinstance(msg, Text):
                self.chat.append(msg)
                return msg

            elif isinstance(msg, Request):
                if msg.label == "reset":
                    if self.instance.engine.is_on():
                        raise PermissionError("Cannot reset while game is ongoing")
                    else:
                        return self.begin()
                elif msg.label == "times":
                    return self.instance.engine.times()
                else:
                    return self.instance.engine.process(msg)

            else:
                raise TypeError(f"Invalid message type {msg.__class__.__name__}")


        except Exception as e:
            return Response.construct(e.__class__.__name__, str(e))

        

class Edge(Serializable):
    def __init__(self, node1 : 'Node', node2 : 'Node'):
        self.nodes = (node1, node2)

        self.instances = []
        self.chat : list[Text] = [] 

        

class Node(Serializable):
    def __init__(self, username : str, password : str):
        self.username = username
        self.password = password

        self.edges : dict[str, Edge]= {}