import datetime

from sqlalchemy import Column, Integer, ForeignKey, Enum, Float, UnicodeText, TIMESTAMP, String
from sqlalchemy.orm import relationship

from mlib.database import Base, Default
from MFramework.database.alchemy.mixins import Snowflake, Cooldown
from .mixins import ItemID, LocationID, EventID, UserID
from . import types
#https://github.com/sqlalchemy/sqlalchemy/wiki/UniqueObject
#https://github.com/sqlalchemy/sqlalchemy/wiki/UniqueObjectValidatedOnPending
# Might be useful for Items
class Location(Default, Cooldown, Base):
    pass


class Event(Default, Base):
    start: datetime.datetime = Column(TIMESTAMP(True))
    end: datetime.datetime = Column(TIMESTAMP(True))
    def __init__(self, name, start, end):
        self.name = name
        self.start = start
        self.end = end

check_type = type
class Item(Default, Cooldown, Base):
    type: types.Item = Column(Enum(types.Item), nullable=False)
    description: str = Column(UnicodeText)
    global_limit: int = Column(Integer)
    rarity: types.Rarity = Column(Enum(types.Rarity))
    worth: int = Column(Integer, default=0)
    durability: int = Column(Integer)
    repairs: int = Column(Integer)
    damage: int = Column(Integer)
    flags: int = Column(Integer, default=0)
    req_skill: int = Column(ForeignKey('Skill.id', ondelete='SET NULL', onupdate='Cascade'))
    
    icon: str = Column(String, nullable=True)
    emoji: str = Column(String, nullable=True)
    def __init__(self, name: str, type: types.Item) -> None:
        super().__init__(name)
        self.type = type if check_type(type) is not str else types.Item.get(type)


class Inventory(ItemID, UserID, Base):
    user_id: Snowflake = Column(ForeignKey("User.id", ondelete='Cascade', onupdate='Cascade'), primary_key=True, nullable=False)
    quantity: int = Column(Integer, default=0)
    item: Item = relationship("Item")
    def __init__(self, Item: Item=None, quantity: int=1):
        self.item = Item
        self.quantity = quantity

class Drop(ItemID, LocationID, EventID, Base):
    location_id: int = Column(ForeignKey("Location.id", ondelete='Cascade', onupdate='Cascade'), primary_key=True)
    weight: float = Column(Float)
    chance: float = Column(Float)
    region_limit: int = Column(Integer)
    quantity_min: int = Column(Integer, default=0)
    quantity_max: int = Column(Integer, default=1)
    
    item: Item = relationship("Item", uselist=False)
    location: Location = relationship("Location", uselist=False)
    event: Event = relationship("Event", uselist=False)

from . import types
class Items:
    Coin = types.Item.Currency
    Crypto = types.Item.Currency

    Material = types.Item.Resource
    Scrap = types.Item.Resource
    Junk = types.Item.Resource
    Trash = types.Item.Resource
    Metal = types.Item.Resource
    Ore = types.Item.Resource
    Ingot = types.Item.Resource

    Liquid = types.Item.Fluid

    Food = types.Item.Resource
    Drink = types.Item.Resource
    Cookie = types.Item.Resource
    Beverage = types.Item.Resource

    Sword = types.Item.Weapon
    Bow = types.Item.Weapon

    Advent = types.Item.Event
    EasterEgg = types.Item.Event

    Upgrade = types.Item.Modification
    Enemy = types.Item.Entity
    NPC = types.Item.Entity
    Ally = types.Item.Entity

