import datetime
from typing import List, Optional

from MFramework.database.alchemy.mixins import ServerID, Snowflake
from mlib.database import ID, Base, Timestamp, TimestampUpdate
from sqlalchemy import (
    Boolean,
    Column,
    Enum,
    ForeignKey,
    Integer,
    Interval,
    String,
    UnicodeText,
)
from sqlalchemy.orm import relationship

from . import types
from .items import Inventory, ItemID
from .mixins import UserID


class Transaction_Inventory(ItemID, UserID, Base):
    """Many to One relationship mapping of users with items and transactions

    Columns
    -------
    id:
        ID of transaction
    item_id:
        ID of item related to this transaction
    user_id:
        ID of user related to item in this transaction
    quantity:
        Amount of items that was transfered
    incoming:
        Whether it's incoming or outgoing item from this user
    """

    user_id: Optional[Snowflake] = Column(ForeignKey("User.id", ondelete="SET NULL", onupdate="Cascade"), nullable=True)
    id: int = Column(ForeignKey("Transaction.id", ondelete="Cascade", onupdate="Cascade"), primary_key=True)
    quantity: int = Column(Integer, default=0)
    incoming: bool = Column(Boolean, default=False, nullable=False)


class Transaction(Timestamp, ServerID, ID, Base):
    """Transactions Table

    Columns
    -------
    id:
        Autoincremented ID of transaction
    server_id:
        ID of server where this transaction took place
    timestamp:
        When this transaction took place
    items:
        Relationship to `Transaction_Inventory` with items that were involved in this transaction
    """

    server_id: Optional[Snowflake] = Column(
        ForeignKey("Server.id", ondelete="SET NULL", onupdate="Cascade"), nullable=True
    )
    items: List[Transaction_Inventory] = relationship(Transaction_Inventory)

    def add(self, to_user_id: Snowflake, item: Inventory):
        """Add incoming `Transaction_Inventory` to this transaction

        Params
        ------
        to_user_id : `Snowflake`
            ID of user that receives this item
        item : `Item`
            `Item` object that is being received"""
        self.items.append(
            Transaction_Inventory(user_id=to_user_id, item_id=item.item.id, quantity=item.quantity, incoming=True)
        )

    def remove(self, from_user_id: Snowflake, item: Inventory):
        """Adds outgoing `Transaction_Inventory` to this transaction

        Params
        ------
        from_user_id : `Snowflake`
            ID of user that sends this item
        item : `Item`
            `Item` object that is being sent"""
        self.items.append(
            Transaction_Inventory(user_id=from_user_id, item_id=item.item.id, quantity=item.quantity, incoming=False)
        )


class Activity(Timestamp, UserID, ServerID, Base):
    """Append-only table storing each activity in separate row

    Columns
    -------
    server_id:
        ID of Server where this activity happened
    user_id:
        ID od User this activity is attattched to
    timestamp:
        Timestamp of this activity
    name:
        Name of this Activity
    value:
        Value of this Activity
    """

    server_id: Snowflake = Column(
        ForeignKey("Server.id", ondelete="Cascade", onupdate="Cascade"), primary_key=True, nullable=False
    )
    user_id: Snowflake = Column(
        ForeignKey("User.id", ondelete="Cascade", onupdate="Cascade"), primary_key=True, nullable=False
    )
    name: types.Statistic = Column(Enum(types.Statistic), primary_key=True)
    value: int = Column(Integer, default=0)


class Log(Timestamp, UserID, ServerID, ID, Base):
    """General Log Table

    Columns
    -------
    id: `int`
    server_id: `Snowflake`
    user_id: `Snowflake`
    timestamp: `datetime.datetime`
        Timestamp of when this happened
    type: `str`
        Name/Type/Category of this log
    value: `str`
        New value that is a result of this action
    """

    user_id: Snowflake = Column(ForeignKey("User.id", ondelete="Cascade", onupdate="Cascade"), nullable=True)
    type: str = Column(String)
    value: str = Column(UnicodeText)


class Statistic(TimestampUpdate, ServerID, UserID, Base):
    """Updateable table

    Columns
    -------
    user_id: `Snowflake`
    server_id: `Snowflake`
    name: `types.Statistic`
    value: `int`
        Current Value of this statistic
    timestamp: `datetime.datetime`
        Timestamp of when this statistic was last updated
    """

    server_id: Snowflake = Column(
        ForeignKey("Server.id", ondelete="Cascade", onupdate="Cascade"), primary_key=True, nullable=False, default=0
    )
    user_id: Snowflake = Column(
        ForeignKey("User.id", ondelete="Cascade", onupdate="Cascade"), primary_key=True, nullable=False, default=0
    )

    name: types.Statistic = Column(Enum(types.Statistic), primary_key=True)
    value: int = Column(Integer, default=0)

    @classmethod
    def get(cls, s, server_id: Snowflake, user_id: Snowflake, name: types.Statistic) -> "Statistic":
        """Get provided statistic for server and user, if doesn't exist create one at 0"""
        r = cls.filter(s, server_id=server_id, user_id=user_id, name=name).first()
        if not r:
            r = cls(server_id=server_id, user_id=user_id, name=name, value=0)
            s.add(r)
        return r

    @classmethod
    def get_or_add(cls, s, server_id: Snowflake, user_id: Snowflake, name: types.Statistic) -> "Statistic":
        """Get provided statistic for server and user, if user or server doesn't exist, create them, and then create statistic at 0"""
        r = cls.fetch_or_add(s, server_id=server_id, user_id=user_id, name=name).first()
        if not r:
            r = cls(server_id=server_id, user_id=user_id, name=name, value=0)
            s.add(r)
        return r

    @classmethod
    def increment(cls, s, server_id: Snowflake, user_id: Snowflake, name: types.Statistic):
        """Increment specified statistic"""
        _s = cls.get(s, server_id, user_id, name)
        _s.value += 1
        s.commit()

    @classmethod
    def decrement(cls, s, server_id: Snowflake, user_id: Snowflake, name: types.Statistic):
        """Decrement specified statistic"""
        _s = cls.get(s, server_id, user_id, name)
        _s.value -= 1
        s.commit()


class Presence(TimestampUpdate, ServerID, UserID, Snowflake, Base):
    """Table with user presences accumulated times.
    Timestamp is updated on last row update

    Columns
    -------
    id : `Snowflake`
    user_id : `str`
    server_id : `Snowflake`
    timestamp : `datetime.datetime`
    type : `types.Statistic`
    name : `str`
    duration : `datetime.timedelta`
    """

    type: types.Statistic = Column(Enum(types.Statistic))
    name: str = Column(String, primary_key=True)
    server_id: Snowflake = Column(ForeignKey("Server.id", onupdate="Cascade", ondelete="Cascade"), primary_key=True)
    user_id: Snowflake = Column(ForeignKey("User.id", onupdate="Cascade", ondelete="Cascade"), primary_key=True)
    duration: datetime.timedelta = Column(Interval)
