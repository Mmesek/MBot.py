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


class Setting(Enum):
    Flags: int = 0  # = enum.IntFlag # Tracking
    Permissions: int = 1  # = enum.IntFlag
    Color: int = 2
    Exp: float = 3
    Voice_Exp: int = 4
    Gender: bool = 5

    Timezone: str = 10
    Birthday: date = 11
    Locale: str = 12
    Region: str = 13
    Currency: float = 14
    Alias: str = 15
    # Channels
    Dynamic: bool = 21
    Buffer: bool = 22
    RPG: bool = 23
    DM_Inbox: bool = 24
    Questions: bool = 25
    # Roles
    Level: int = 31
    Reaction: str = 32
    Presence: str = 33
    Custom: Snowflake = 34
    Activity: int = 35
    Voice_Link: Snowflake = 36
    Special: str = 37
    Group: str = 38
    Nitro: Snowflake = 39

    ServerID: Snowflake = 40
    ChannelID: Snowflake = 41
    MessageID: Snowflake = 42
    RoleID: Snowflake = 43
    UserID: Snowflake = 44
    # Server
    Allowed_Duplicated_Messages: int = 50
    Should_Remove_Links: bool = 51
    Auto_Mute_Infractions: int = 52
    Auto_Mute_Duration: str = 53
    Auto_Ban_Infractions: int = 54
    Limit_Nitro_Roles: int = 55
    Stream: str = 60


class Flags(enum.IntFlag):
    Chat = 1 << 0
    Voice = 1 << 1
    Presence = 1 << 2
    Activity = 1 << 3
    Nitro = 1 << 4
