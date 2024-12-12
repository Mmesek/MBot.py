from MFramework import Groups
from mlib.types import Enum


class Permissions(bytes, Enum):
    @property
    def permission(cls) -> Groups:
        return cls.__annotations__.get(cls.name, Groups.SYSTEM)

    def __new__(cls, value: int, doc=None):
        obj = bytes.__new__(cls, [value])
        obj._value_ = value
        obj.doc = doc
        return obj

    def __init__(self, value="Missing value", doc="Missing docstring") -> None:
        self._value_ = value
        self.doc = doc
