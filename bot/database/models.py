import re
from datetime import datetime, timedelta
from typing import Annotated, Optional

from MFramework import Snowflake
from MFramework.commands import Groups
from MFramework.database.alchemy.mixins import ChannelID, ServerID
from MFramework.database.alchemy.mixins import Snowflake as db_Snowflake
from mlib.database import Base, File, Timestamp, TimestampUpdate
from mlib.logger import log
from sqlalchemy import TIMESTAMP, BigInteger, Enum, ForeignKey, Interval, UnicodeText
from sqlalchemy.orm import Mapped, MappedAsDataclass, declared_attr
from sqlalchemy.orm import mapped_column as Column
from sqlalchemy.orm import relationship

from bot.database import types


class Eigth_columns:
    def __init_subclass__(cls):
        columns = [len(base.__annotations__) for base in cls.__bases__]
        columns.append(len(cls.__annotations__))
        if sum(columns) < 8:
            log.log(5, "Table %s is using %s/8 columns", cls.__name__, sum(columns))
        return super().__init_subclass__()


exp_rate_ = Annotated[Optional[float], Column(default=None)]
flags_ = Annotated[Optional[int], Column(default=0)]
type_ = Annotated[str | None, Column(default=None)]


class ExpRate(MappedAsDataclass):
    exp_rate: Mapped[exp_rate_] = Column(default=None)
    """XP points to be granted"""


class Flags(MappedAsDataclass):
    flags: Mapped[flags_] = Column(default=None)


class Server(ExpRate, Flags, db_Snowflake, Eigth_columns, Base):
    """Servers table representing server in Database"""

    premium: Mapped[bool] = Column(default=False)
    alias: Mapped[Optional[str]] = Column(default=None)
    auto_mute: Mapped[Optional[int]] = Column(default=None)
    mute_duration: Mapped[Optional[timedelta]] = Column(default=None)
    auto_ban: Mapped[Optional[int]] = Column(default=None)


class Subscription(Base):
    webhook_id: Mapped[int] = Column(ForeignKey("Webhook.id", ondelete="Cascade", onupdate="Cascade"), primary_key=True)
    thread_id: Mapped[int | None] = Column(BigInteger)
    source: Mapped[str] = Column(primary_key=True)
    pattern: Mapped[str] = Column(primary_key=True, default="", kw_only=True)
    content: Mapped[str | None] = Column(default=None)

    regex: re.Pattern | None = None

    def compile(self):
        self.regex = re.compile(self.pattern)


class Webhook(ChannelID, ServerID, db_Snowflake, Base):
    token: Mapped[str]
    subscriptions: Mapped[list[Subscription]] = relationship(
        foreign_keys="Subscription.webhook_id", kw_only=True, default_factory=list
    )


class User(ExpRate, Flags, db_Snowflake, Eigth_columns, Base):
    """Users table representing user in Database"""

    supporter: Mapped[bool] = Column(default=False)
    birthday: Mapped[datetime | None] = Column(default=None)
    timezone: Mapped[str | None] = Column(default=None)
    # NOTE 2 more slots available

    statistics: Mapped[list["Statistic"]] = relationship(
        foreign_keys="Statistic.user_id", back_populates="user", default_factory=list, lazy=True
    )
    snippets: Mapped[list["Snippet"]] = relationship(
        foreign_keys="Snippet.user_id", back_populates="user", default_factory=list, lazy=True
    )
    tasks: Mapped[list["Task"]] = relationship(
        foreign_keys="Task.user_id", back_populates="user", default_factory=list, lazy=True
    )


class UserID(MappedAsDataclass):
    user_id: Mapped[int] = Column(
        BigInteger, ForeignKey("User.id", ondelete="Cascade", onupdate="Cascade"), primary_key=False, nullable=False
    )

    @declared_attr
    def user(cls) -> Mapped[User]:
        return relationship(lazy=True)  # foreign_keys=f"{cls.__name__}.user_id",


class Statistic(TimestampUpdate, Base):
    server_id: Mapped[int] = Column(
        BigInteger, ForeignKey("Server.id", ondelete="Cascade", onupdate="Cascade"), primary_key=True, nullable=False
    )
    user_id: Mapped[int] = Column(
        BigInteger, ForeignKey("User.id", ondelete="Cascade", onupdate="Cascade"), nullable=False, primary_key=True
    )
    type: Mapped[type_] = Column(primary_key=True)
    name: Mapped[Optional[str]] = Column(primary_key=True, nullable=True, default=None)
    value: Mapped[int] = Column(default=0)

    user: Mapped[User] = relationship(back_populates="statistics", lazy=True, default=None)


class Role(ExpRate, Flags, ServerID, db_Snowflake, Eigth_columns, Base):
    """Roles table representing role in Database"""

    type: Mapped[type_] = Column(default=None)
    permissions: Mapped[Groups] = Column(Enum(Groups), default=None)
    exp_req: Mapped[float | None] = Column(default=None)
    string: Mapped[str | None] = Column(default=None)
    """Wildcard for Presence or reaction, to be discriminated by type or flags TODO"""


class Channel(ExpRate, Flags, ServerID, db_Snowflake, Eigth_columns, Base):
    """Channels table representing channel in Database"""

    type: Mapped[type_] = Column(default=None)
    # NOTE: 3 more slots available


class Snippet(Timestamp, File, UserID, ServerID, Eigth_columns, Base):
    """Snippets related to Server"""

    role_id: Mapped[Snowflake | None] = Column(ForeignKey("Role.id", ondelete="SET NULL", onupdate="Cascade"))
    group: Mapped[Groups] = Column(Enum(Groups))
    type: Mapped[types.Snippet] = Column(Enum(types.Snippet))
    name: Mapped[str]
    trigger: Mapped[str]
    content: Mapped[str | None] = Column(UnicodeText)
    cooldown: Mapped[timedelta | None] = Column(Interval)
    locale: Mapped[str]


class Task(Timestamp, ServerID, ChannelID, Eigth_columns, Base):
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

    user: Mapped[User] = relationship(back_populates="tasks", lazy=True, default=None)
