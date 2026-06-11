# Demetre Seturidze
# Chess
# Serialization

import json
from typing import Type, Dict, Optional 
from abc import abstractmethod
import numpy as np

PrimitiveJSONType = dict | list | str | float | int | bool | None

class Serializable:
    # serializes this object into a dictionary
    @abstractmethod
    def to_dict(self) -> dict:
        pass 

    # deserializes according to the given dictionary
    @classmethod 
    @abstractmethod 
    def from_dict(cls, dct : dict) -> Optional['Serializable']:
        return cls(**dct)
    
    # recursively finds and maps all available serializable subclasses
    @classmethod
    def get_subclass_registry(cls) -> Dict[str, Type['Serializable']]:
        registry = {}
        for subclass in cls.__subclasses__():
            registry[subclass.__name__] = subclass
            registry.update(subclass.get_subclass_registry())
        return registry

SerialType = PrimitiveJSONType | Serializable

NP_INT = (np.int8, np.int16, np.int32, np.int64)
NP_FLOAT = (np.float16, np.float32, np.float64)
NP_COMPLEX = (np.complex64, np.complex128)

def to_native(obj):
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    
    # 2. Handle all NumPy scalars (int, float, bool, complex)
    elif isinstance(obj, NP_INT):
        return int(obj)
    elif isinstance(obj, NP_FLOAT):
        return float(obj)
    elif isinstance(obj, NP_COMPLEX):
        return complex(obj)
    elif isinstance(obj, np.bool):
        return bool(obj)
    
    # Return native objects (int, float, str, bool, None) as-is
    return obj


# JSON encoder/decoder for serializable objects
class Encoder(json.JSONEncoder):
    def default(self, obj : SerialType | np.ndarray):
        if isinstance(obj, Serializable):
            # includes the type of the object for deserialization
            objdict = obj.to_dict()
            objdict['__type__'] = obj.__class__.__name__
            return objdict

        return super().default(to_native(obj))

class Decoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        super().__init__(object_hook=self.object_hook, *args, **kwargs)
    
    def object_hook(self, dct : dict):
        # look for our special type tag in the parsed dictionary
        if "__type__" in dct:
            type_name = dct.pop("__type__")
            registry = Serializable.get_subclass_registry()
            
            # Match the tag to the class and instantiate it
            if type_name in registry:
                target_class = registry[type_name]
                return target_class.from_dict(dct)
                
        return dct


def serialize(
    obj : SerialType,
    skipkeys: bool = False,
    ensure_ascii: bool = True,
    check_circular: bool = True,
    allow_nan: bool = True,
    indent: int | str | None = None,
    separators: tuple[str, str] | None = None,
    sort_keys: bool = False,
    **kwargs
) -> str:
    return json.dumps(obj, cls=Encoder, skipkeys=skipkeys, ensure_ascii=ensure_ascii, check_circular=check_circular,allow_nan=allow_nan, indent=indent, separators=separators, sort_keys=sort_keys, **kwargs)

def deserialize(
    s : str, 
) -> SerialType:
    return json.loads(s, cls=Decoder)