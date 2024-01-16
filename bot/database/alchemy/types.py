import enum
from datetime import date

from mdiscord import Snowflake
from MFramework.commands import Groups
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


class Flags(enum.IntFlag):
    Chat = 1 << 0
    Voice = 1 << 1
    Presence = 1 << 2
    Activity = 1 << 3
    Nitro = 1 << 4
