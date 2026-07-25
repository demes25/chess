# Demetre Seturidze
# Chess
# Protocol


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

class Wrapper(Generic[T]):
    _type : type

    __item__ : T
    __attrs__ : tuple[str]

    def __init__(self, item : T, *attrs : str):
        object.__setattr__(self, '__item__', item)
        object.__setattr__(self, '__attrs__', tuple(attrs))

        super().__init__()

    def __getattr__(self, name : str):
        return getattr(self.__item__, name)

    def __setattr__(self, name : str, value):
        if name in self.__attrs__:
            object.__setattr__(self, name, value)
        else:
            setattr(self.__item__, name, value)

    
    @classmethod
    def construct(cls, *args, **kwargs):
        return cls(cls._type(*args, **kwargs))

