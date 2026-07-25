from .pyutils import Grid, Wrapper, Index
from . import engine
from .engine import load_figures, load_sets

from netlib.serialization import Serializable

RANK = 2
NUM_PLAYERS = 2


class Response(Wrapper[engine.Response], Serializable):
    _type = engine.Response

    def __init__(self, item : engine.Response):
        super().__init__(item)

    def to_dict(self):
        dct = {
            "label" : self.__item__.label
        }

        if self.__item__.content is not None:
            dct["content"] = self.__item__.content
        
        return dct
    
class Request(Wrapper[engine.Request], Serializable):
    _type = engine.Request 

    def __init__(self, item : engine.Request):
        super().__init__(item)

    def to_dict(self):
        dct = {
            "label" : self.label
        }

        if self.content is not None:
            dct["content"] = self.content
        
        return dct

class Event(Wrapper[engine.Event], Serializable):
    _type = engine.Event

    def __init__(self, item : engine.Event):
        super().__init__(item)

    def to_dict(self):
        dct = {
            "actions" : self.__item__.actions
        }

        if self.__item__.times is not None:
            dct["times"] = self.__item__.times

        if self.__item__.duration is not None:
            dct["duration"] = self.__item__.duration

        if self.__item__.checks is not None:
            dct["checks"] = self.__item__.checks
        
        if self.__item__.die is not None:
            dct["die"] = self.__item__.die 
        
        if self.__item__.promote is not None:
            dct["promote"] = self.__item__.promote

        if self.__item__.end is not None:
            dct["end"] = self.__item__.end

        return dct



class Engine(Wrapper[engine.Engine]): #, Serializable):
    _type = engine.Engine 

    def __init__(self, item : engine.Engine):
        super().__init__(item)

    
    def process(self, request : Request) -> Response | Event:
        resp = self.__item__.process(request.__item__)

        if isinstance(resp, engine.Response):
            return Response(resp)
        else:
            return Event(resp)

    def times(self) -> Response:
        return Response(self.__item__.times())

    @staticmethod
    def disembed(jstr) -> 'Engine':
        return Engine(engine.Engine.disembed(jstr))


        

    
__all__ = ["Indent", "Response", "Request", "Event", "Engine", "Grid", "load_figures", "load_sets"]