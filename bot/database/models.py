from datetime import datetime, timedelta

from MFramework.commands import Groups
from MFramework.database.alchemy.mixins import ChannelID, RoleID, ServerID, Snowflake
from mlib.database import Base, File, Timestamp
from sqlalchemy import (
    TIMESTAMP,
    BigInteger,
    Boolean,
    Column,
    Enum,
    ForeignKey,
    Integer,
    Interval,
    String,
    UnicodeText,
)
from sqlalchemy.orm import declared_attr

from bot.database import types


class UserID:
    @declared_attr
    def user_id(cls) -> int:
        return Column(ForeignKey("User.id", ondelete="Cascade", onupdate="Cascade"), primary_key=False, nullable=False)

    # @declared_attr
    # def user(cls):
    #    return relationship("User", foreign_keys=f"{cls.__name__}.user_id", lazy=True)


class ExpRate:
    exp_rate: float = None
    """XP points to be granted"""


class Flags:
    flags: int = None


class Server(ExpRate, Flags, Snowflake, Base):
    """Servers table representing server in Database"""

    premium: bool = None
    alias: str = None
    auto_mute: int = None
    mute_duration: timedelta = None
    auto_ban: int = None


class User(ExpRate, Flags, Snowflake, Base):
    """Users table representing user in Database"""

    supporter: bool = None
    birthday: datetime = None
    timezone: str = None
    # NOTE 2 more slots available


class Role(ExpRate, Flags, ServerID, Snowflake, Base):
    """Roles table representing role in Database"""

    permissions: Groups = None  # = Column(Enum(Groups))
    type: str = None
    exp_req: float = None
    string: str = None
    """Wildcard for Presence or reaction, to be discriminated by type or flags TODO"""


class Channel(ExpRate, Flags, ServerID, Snowflake, Base):
    """Channels table representing channel in Database"""

    type: str = None
    # NOTE: 3 more slots available


class Snippet(Timestamp, File, RoleID, UserID, ServerID, Base):
    """Snippets related to Server"""

    role_id: Snowflake = Column(ForeignKey("Role.id", ondelete="SET NULL", onupdate="Cascade"))
    group: Groups = Column(Enum(Groups))
    type: types.Snippet = Column(Enum(types.Snippet))
    name: str = Column(String)
    trigger: str = Column(String)
    content: str = Column(UnicodeText)
    cooldown: timedelta = Column(Interval)
    locale: str = Column(String)


class Task(Timestamp, ServerID, ChannelID, UserID, Base):
    """Tasks that were scheduled for a bot"""

    user_id: Snowflake = Column(
        ForeignKey("User.id", ondelete="Cascade", onupdate="Cascade"), primary_key=True, nullable=False
    )
    message_id: Snowflake = Column(BigInteger, primary_key=True, autoincrement=False)

    finished: bool = Column(Boolean, default=False)
    type: types.Task = Column(Enum(types.Task))
    end: datetime = Column(TIMESTAMP(True))

    title: str = Column(String)
    description: str = Column(UnicodeText)
    count: str = Column(Integer)
