from typing import List

from mlib.database import ID, Base, Default
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, UnicodeText
from sqlalchemy.orm import relationship

from .mixins import CharacterID, ItemID, SkillID, UserID


class Skill(Default, Base):
    pass


class Character(UserID, ID, Base):
    name: str = Column(String)
    race: str = Column(String)
    gender: bool = Column(Boolean)
    age: int = Column(Integer)
    color: int = Column(Integer)

    profession: str = Column(String)
    place_of_origin: str = Column(UnicodeText)
    story: str = Column(UnicodeText)

    drink: str = Column(String)
    hate: str = Column(String)
    fear: str = Column(String)
    weakness: str = Column(String)
    strength: str = Column(String)
    skills: List["Character_Skills"] = relationship("Character_Skills")
    items: List["Character_Items"] = relationship("Character_Items")


class Character_Skills(SkillID, CharacterID, Base):
    skill_id: int = Column(ForeignKey("Skill.id", ondelete="Cascade", onupdate="Cascade"), primary_key=True)
    exp: int = Column(Integer, default=0)


class Character_Items(ItemID, CharacterID, Base):
    quantity: int = Column(Integer, default=0)
