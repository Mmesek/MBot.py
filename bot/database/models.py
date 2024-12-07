from datetime import datetime, timedelta

from MFramework.commands import Groups
from MFramework.database.alchemy.mixins import ChannelID, RoleID, ServerID, Snowflake
from mlib.database import Base, File, Timestamp
from sqlalchemy import (
    TIMESTAMP,
    BigInteger,
    Enum,
    ForeignKey,
    Interval,
    String,
    UnicodeText,
)
from sqlalchemy.orm import Mapped, declared_attr
from sqlalchemy.orm import mapped_column as Column

from bot.database import types


class UserID:
    @declared_attr
    def user_id(cls) -> Mapped[int]:
        return Column(ForeignKey("User.id", ondelete="Cascade", onupdate="Cascade"), primary_key=False, nullable=False)

    # @declared_attr
    # def user(cls):
    #    return relationship("User", foreign_keys=f"{cls.__name__}.user_id", lazy=True)


class ExpRate:
    exp_rate: Mapped[float]
    """XP points to be granted"""


class Flags:
    flags: Mapped[int]


class Server(ExpRate, Flags, Snowflake, Base):
    """Servers table representing server in Database"""

    premium: Mapped[bool]
    alias: Mapped[str]
    auto_mute: Mapped[int]
    mute_duration: Mapped[timedelta]
    auto_ban: Mapped[int]


class User(ExpRate, Flags, Snowflake, Base):
    """Users table representing user in Database"""

    supporter: Mapped[bool]
    birthday: Mapped[datetime]
    timezone: Mapped[str]
    # NOTE 2 more slots available


class Role(ExpRate, Flags, ServerID, Snowflake, Base):
    """Roles table representing role in Database"""

    permissions: Mapped[Groups] = Column(Enum(Groups))
    type: Mapped[str]
    exp_req: Mapped[float]
    string: Mapped[str]
    """Wildcard for Presence or reaction, to be discriminated by type or flags TODO"""


class Channel(ExpRate, Flags, ServerID, Snowflake, Base):
    """Channels table representing channel in Database"""

    type: Mapped[str]
    # NOTE: 3 more slots available


class Snippet(Timestamp, File, RoleID, UserID, ServerID, Base):
    """Snippets related to Server"""

    role_id: Mapped[Snowflake] = Column(ForeignKey("Role.id", ondelete="SET NULL", onupdate="Cascade"))
    group: Mapped[Groups] = Column(Enum(Groups))
    type: Mapped[types.Snippet] = Column(Enum(types.Snippet))
    name: Mapped[str] = Column(String)
    trigger: Mapped[str] = Column(String)
    content: Mapped[str] = Column(UnicodeText)
    cooldown: Mapped[timedelta] = Column(Interval)
    locale: Mapped[str] = Column(String)


class Task(Timestamp, ServerID, ChannelID, UserID, Base):
    """Tasks that were scheduled for a bot"""

    user_id: Mapped[Snowflake] = Column(
        ForeignKey("User.id", ondelete="Cascade", onupdate="Cascade"), primary_key=True, nullable=False
    )
    message_id: Mapped[Snowflake] = Column(BigInteger, primary_key=True, autoincrement=False)
    type: Mapped[types.Task] = Column(Enum(types.Task))
    end: Mapped[datetime] = Column(TIMESTAMP(True))
    title: Mapped[str]
    description: Mapped[str] = Column(UnicodeText)
    count: Mapped[int]

    finished: Mapped[bool] = Column(default=False)
