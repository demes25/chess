from .pyutils import Grid, Wrapper, SerialWrapper, Index
from . import internals
from .internals import load_figures, load_sets

RANK = 2
NUM_PLAYERS = 2


class EngineResponse(SerialWrapper[internals.Response]):
    _type = internals.Response

    def __init__(self, item : internals.Response):
        super().__init__(item)

    def to_dict(self):
        dct = {
            "label" : self.__item__.label
        }

        if self.__item__.content is not None:
            dct["content"] = self.__item__.content
        
        return dct
    
class EngineRequest(SerialWrapper[internals.Request]):
    _type = internals.Request 

    def __init__(self, item : internals.Request):
        super().__init__(item)

    def to_dict(self):
        dct = {
            "label" : self.__item__.label
        }

        if self.__item__.content is not None:
            dct["content"] = self.__item__.content
        
        return dct

    @classmethod
    def from_dict(cls, dct):
        return cls.construct(**dct) 

class EngineEvent(SerialWrapper[internals.Event]):
    _type = internals.Event

    def __init__(self, item : internals.Event):
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

    @classmethod
    def from_dict(cls, dct):
        return cls.construct(**dct)
    
class EngineError(SerialWrapper[internals.Error]):
    _type = internals.Error

    def __init__(self, item : internals.Error):
        super().__init__(item)

    def to_dict(self):
        dct = {
            "label" : self.__item__.label
        }

        if self.__item__.content is not None:
            dct["content"] = self.__item__.content

        return dct

    @classmethod
    def from_dict(cls, dct):
        return cls.construct(**dct)

class Engine(Wrapper[internals.Engine]): #, Serializable):
    _type = internals.Engine 

    def __init__(self, item : internals.Engine):
        super().__init__(item)

    
    def process(self, request : EngineRequest) -> EngineResponse | EngineEvent:
        resp = self.__item__.process(request.__item__)

        if isinstance(resp, internals.Response):
            return EngineResponse(resp)
        elif isinstance(resp, internals.Error):
            return EngineError(resp)
        else:
            return EngineEvent(resp)

    def times(self) -> EngineResponse:
        return EngineResponse(self.__item__.times())

    @staticmethod
    def disembed(jstr) -> 'Engine':
        return Engine(internals.Engine.disembed(jstr))


        

    
__all__ = ["Index", "EngineResponse", "EngineRequest", "EngineEvent", "Engine", "Grid", "load_figures", "load_sets"]