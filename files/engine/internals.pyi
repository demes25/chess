from typing import Sequence

def load_figures(filepath : str) -> None: ...

def load_sets(filepath : str) -> None: ...


class Request:
    label : str 
    content : str | tuple[Sequence[int], Sequence[int]] | int | None 

    def __init__(self, label : str, content : str | tuple[Sequence[int], Sequence[int]] | int | None = None) -> None: ...

class Response:
    label : str 
    content : str | Sequence[float] | None = None

    def __init__(self, label : str, content : str | Sequence[float] | None = None) -> None: ...

class Event:
    actions : Sequence[tuple[Sequence[int], Sequence[int]]]
    times : Sequence[float] | None
    duration : float | None 
    checks : Sequence[int] | None 
    die : Sequence[int] | None 
    promote : int | None 
    end : str | None 

    def __init__(
        self,
        actions : Sequence[tuple[Sequence[int], Sequence[int]]],
        times : Sequence[float] | None = None,
        duration : float | None = None,
        checks : Sequence[int] | None = None,
        die : Sequence[int] | None = None,
        promote : int | None = None,
        end : str | None = None 
    ) -> None : ...

class Error:
    label : str
    content : str = None

    def __init__(self, label : str, content : str | None = None) -> None: ... 

class Engine:
    
    def __init__(self, set_name: str, timer : float) -> None: ...

    def layout(self) -> str: ...
    
    def times(self) -> Response: ...
    def process(self, request: Request) -> Response | Event | Error: ...
    def is_on(self) -> bool: ...

    def embed(self) -> str: ...

    @staticmethod
    def disembed(jstr : str) -> Engine: ...

    def __str__(self) -> str: ...

