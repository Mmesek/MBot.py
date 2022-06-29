from sqlalchemy import Column, ForeignKey
from sqlalchemy.orm import declared_attr, relationship


class UserID:
    @declared_attr
    def user_id(cls) -> int:
        return Column(ForeignKey("User.id", ondelete="Cascade", onupdate="Cascade"), primary_key=False, nullable=False)

    # @declared_attr
    # def user(cls):
    #    return relationship("User", foreign_keys=f"{cls.__name__}.user_id", lazy=True)


class SkillID:
    @declared_attr
    def skill_id(cls) -> int:
        return Column(ForeignKey("Skill.id", ondelete="SET NULL", onupdate="Cascade"), primary_key=True)

    @declared_attr
    def skill(cls):
        return relationship("Skill", foreign_keys=f"{cls.__name__}.skill_id", lazy=True)


class CharacterID:
    @declared_attr
    def character_id(cls) -> int:
        return Column(ForeignKey("Character.id", ondelete="Cascade", onupdate="Cascade"), primary_key=True)

    # @declared_attr
    # def character(cls):
    #    return relationship("Character", foreign_keys=f"{cls.__name__}.character_id", lazy=True)


class LocationID:
    @declared_attr
    def location_id(cls) -> int:
        return Column(ForeignKey("Location.id", ondelete="Cascade", onupdate="Cascade"))

    @declared_attr
    def location(cls):
        return relationship("Location", foreign_keys=f"{cls.__name__}.location_id", lazy=True)


class EventID:
    @declared_attr
    def event_id(cls) -> int:
        return Column(ForeignKey("Event.id", ondelete="SET NULL", onupdate="Cascade"))

    @declared_attr
    def event(cls):
        return relationship("Event", foreign_keys=f"{cls.__name__}.event_id", lazy=True)


class ItemID:
    @declared_attr
    def item_id(cls) -> int:
        return Column(ForeignKey("Item.id", ondelete="Cascade", onupdate="Cascade"), primary_key=True)

    @declared_attr
    def item(cls):
        return relationship("Item", foreign_keys=f"{cls.__name__}.item_id", lazy=True)
