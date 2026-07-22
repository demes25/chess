# Demetre Seturidze
# Chess
# Protocol

from dataclasses import dataclass
from netlib.serialization import Serializable

from typing import Sequence, Generic, TypeVar

from collections.abc import Iterable, Iterator

T = TypeVar("T")
Index = Sequence[int]

class Grid(Generic[T], Iterable[T]):
    def __init__(self, dims : Index):

        assert 0 not in dims

        self._rank = len(dims)
        self._shape = tuple(dims)
        _sizes = [1] * self._rank

        for i in range(self._rank-2, -1, -1):
            _sizes[i] = self._shape[i+1]*_sizes[i+1]
        
        self._sizes = tuple(_sizes)

        self._capacity = self._shape[0]*_sizes[0]

        self._arr = [None] * self._capacity
    
    
    @property
    def rank(self) -> int:
        return self._rank 
    
    @property
    def shape(self) -> Index:
        return self._shape
    
    @property
    def sizes(self) -> Index:
        return self._sizes
    
    @property
    def capacity(self) -> Index:
        return self._capacity
    

    def collapse(self, tup : Index) -> int:
        if len(tup) != len(self._shape):
            raise IndexError("Shape mismatch.")
        
        collapsed = 0

        for i in range(len(tup)):
            if 0 <= tup[i] < self._shape[i]:
                collapsed += (tup[i] * self._sizes[i])
            else:
                raise IndexError("Out of bounds.")
        
        return collapsed

    def __iter__(self) -> Iterator[T]:
        i = 0

        while(i < self._capacity):
            current = self._arr[i]

            if current is not None:
                yield current
            
            i += 1




    def __getitem__(self, index : Index | int) -> T:
        if isinstance(index, (tuple, list)):
            index = self.collapse(index)
        
        return self._arr[index]
    
    def __setitem__(self, index : Index | int, value : T):
        if isinstance(index, (tuple, list)):
            index = self.collapse(index)
        
        self._arr[index] = value 
    


@dataclass 
class Text(Serializable):
    content : str
    index : int

    def to_dict(self):
        return {
            "content" : self.content,
            "index" : self.index
        }

@dataclass
class Chat(Serializable):
    content : list[Text]

    def to_dict(self):
        return {
            "content" : self.content
        }
    
@dataclass
class Response(Serializable):
    label : str
    content : str | None = None

    def to_dict(self):
        dct = {
            "label" : self.label
        }

        if self.content is not None:
            dct["content"] = self.content
        
        return dct
    
@dataclass
class Request(Serializable):
    index : int 
    content : str 

    def to_dict(self):
        return {
            "index" : self.index,
            "content" : self.content
        }

@dataclass
class Action(Serializable):
    start : Index
    end : Index

    def to_dict(self):
        return {
            "start" : self.start,
            "end" : self.end
        }

@dataclass
class Promotion(Serializable):
    index : int

    def to_dict(self):
        return {
            "index" : self.index 
        }
    
@dataclass
class Event(Serializable):
    action : Action
    times : Sequence[float]
    duration : float 
    end : str | None = None
    checks : list | None = None
    coaction : Action | None = None
    die : Index | None = None 
    promote : int | None = None 

    def to_dict(self):
        dct = {
            "action" : self.action,
            "times" : self.times,
            "duration" : self.duration,
        }

        if self.end is not None:
            dct["end"] = self.end

        if self.checks is not None:
            dct["checks"] = self.checks

        if self.coaction is not None:
            dct["coaction"] = self.coaction
        
        if self.die is not None:
            dct["die"] = self.die 
        
        if self.promote is not None:
            dct["promote"] = self.promote



InMessage = Text | Chat | Event | Response
OutMessage = Text | Chat | Action | Promotion | Request