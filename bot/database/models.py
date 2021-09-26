from __future__ import annotations
from typing import List
from datetime import timedelta, datetime

from sqlalchemy import Column, String, Integer, BigInteger, Interval, Enum, Boolean, UnicodeText, TIMESTAMP, ForeignKey
from sqlalchemy.orm import relationship

from MFramework.database.alchemy.table_mixins import HasDictSettingsRelated
from MFramework.database.alchemy.mixins import Snowflake, ServerID, ChannelID, RoleID

from mlib.database import Base, File, Timestamp

from .mixins import UserID
from . import Inventory
from . import log, types

class User(HasDictSettingsRelated, Snowflake, Base):
    '''Users table representing user in Database

    Columns
    -------
    id: `Snowflake`'''
    infractions: List[log.Infraction] = relationship("Infraction", back_populates="user", foreign_keys="Infraction.user_id", order_by="desc(Infraction.timestamp)")
    mod_actions: List[log.Infraction] = relationship("Infraction", back_populates="moderator", foreign_keys="Infraction.moderator_id", order_by="desc(Infraction.timestamp)")
    transactions: List[log.Transaction] = relationship("Transaction_Inventory", order_by="desc(Transaction.timestamp)")
    activities: List[log.Activity] = relationship("Activity", order_by="desc(Activity.timestamp)")
    statistics: List[log.Statistic] = relationship("Statistic")

    items: List[Inventory] = relationship('Inventory')
    def __init__(self, id) -> None:
        self.id = id
    
    def add_item(self, *items: Inventory, transaction: log.Transaction = None):
        '''Add `Inventory.item` to this `User` and optionally to `Transaction`'''
        for item in items:
            if transaction:
                transaction.add(self.id, item)
            for owned_item in self.items:
                if item.item.name == owned_item.item.name:
                    owned_item.quantity += item.quantity
                    continue
            self.items.append(item)

    def remove_item(self, *items: Inventory, transaction: log.Transaction = None):
        '''Removes `Inventory.item` from this `User` and optionally adds it as outgoing to `Transaction`'''
        for item in items:
            if transaction:
                transaction.remove(self.id, item)
            for owned_item in self.items:
                if item.item.name == owned_item.item.name:
                    owned_item.quantity -= item.quantity
                    if owned_item.quantity == 0:
                        self.items.remove(item) # No idea if it'll work
                        #pass # TODO: Remove from mapping/association or something
                    continue

    def add_infraction(self, server_id: int, moderator_id: int, type: types.Infraction, reason: str=None, duration: timedelta=None, channel_id: int=None, message_id: int=None, active: bool=True) -> List[log.Infraction]:
        '''
        Add infraction to current user. Returns total user infractions on server
        '''
        self.infractions.append(log.Infraction(server_id = server_id, moderator_id = moderator_id, type=type, reason=reason, duration=duration, channel_id=channel_id, message_id=message_id, active=active))
        return [i for i in self.infractions if i.server_id == server_id]
    
    def transfer(self, server_id: int, recipent: User, sent: List[Inventory] = None, recv: List[Inventory] = None, remove_item:bool=True, turn_item:bool=False) -> log.Transaction:
        '''
        Transfers item from current user to another user & returns transaction log (Which needs to be added to session manually[!])

        Params
        ------
        server_id:
            ID of Server on which transfer is happening
        recipent:
            User object (DB one) which receives the items
        sent:
            Inventory object containing item that should be removed from current user and added to remote user
        recv:
            Inventory object containing item that should be added to current user and removed from remote user
        remove_item: 
            Whether it should remove item from another user 
            (Sent removed from current user and/or Received removed from another user, useful for exchanges)
        turn_item:
            Whether it should remove received item from current user 
            (Useful when turning item from one to another on same user)
        '''
        transaction = log.Transaction(server_id = server_id)
        if sent: #TODO: Multiple different items/inventories for sent/recv 
            recipent.add_items(sent, transaction)
            if remove_item and not turn_item:
                self.remove_items(sent, transaction)
        if recv:
            if not turn_item:
                self.add_items(recv, transaction)
            else:
                self.remove_items(recv, transaction)
            if remove_item and not turn_item:
                recipent.remove_items(recv, transaction)
        return transaction
    def claim_items(self, server_id: int, items: List[Inventory]) -> log.Transaction:
        return self.transfer(server_id, None, recv=items, remove_item=False)
    def gift_items(self, server_id: int, recipent: User, items: List[Inventory]) -> log.Transaction:
        return self.transfer(server_id, recipent, items)
    def turn_race(self, server_id: int, recipent: User, from_race: types.HalloweenRaces, into_race: types.HalloweenRaces) -> log.Transaction:
        return self.transfer(server_id, recipent, [from_race], [into_race], False, True) # That is definitly not what was planned #FIXME

from MFramework.commands._utils import Groups
class Snippet(Timestamp, File, RoleID, UserID, ServerID, Base):
    '''Snippets related to Server'''
    role_id: Snowflake = Column(ForeignKey("Role.id", ondelete='SET NULL', onupdate='Cascade'))
    group: Groups = Column(Enum(Groups))
    type: types.Snippet = Column(Enum(types.Snippet))
    name: str = Column(String)
    trigger: str = Column(String)
    content: str = Column(UnicodeText)
    cooldown: timedelta = Column(Interval)
    locale: str = Column(String)

class Task(Timestamp, ServerID, ChannelID, UserID, Base):
    '''Tasks that were scheduled for a bot'''
    user_id: Snowflake = Column(ForeignKey("User.id", ondelete='Cascade', onupdate='Cascade'), primary_key=True, nullable=False)
    message_id: Snowflake = Column(BigInteger, primary_key=True, autoincrement=False)

    finished: bool = Column(Boolean, default=False)
    type: types.Task = Column(Enum(types.Task))
    end: datetime = Column(TIMESTAMP(True))

    title: str = Column(String)
    description: str = Column(UnicodeText)
    count: str = Column(Integer)
