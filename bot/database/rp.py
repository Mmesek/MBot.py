from typing import List

from sqlalchemy.orm import relationship
from sqlalchemy import Column, String, Integer, Boolean, UnicodeText, ForeignKey

from mlib.database import Base, Default, ID

from .mixins import ItemID, SkillID, CharacterID, UserID

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
    skills: List['Character_Skills'] = relationship("Character_Skills")
    items: List['Character_Items'] = relationship("Character_Items")


class Character_Skills(SkillID, CharacterID, Base):
    skill_id: int = Column(ForeignKey("Skill.id", ondelete='Cascade', onupdate='Cascade'), primary_key=True)
    exp: int = Column(Integer, default=0)


class Character_Items(ItemID, CharacterID, Base):
    quantity: int = Column(Integer, default=0)
