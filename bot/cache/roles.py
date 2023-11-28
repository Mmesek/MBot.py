from MFramework.cache.guild import Base, ObjectCollections
from sqlalchemy.orm import Query, Session

from bot.database import models as db
from MFramework import Bot, Groups, Guild, Snowflake

from ..database import models as db
from ..database.alchemy import types
from .database import Database, fetch_or_add


class Roles(Database, ObjectCollections, Base):
    voice_link: Snowflake = None
    """Ephemeral Role to grant when user is connected to a Voice channel"""

    async def initialize(self, *, bot: Bot, guild: Guild, session: Session, **kwargs) -> None:
        await super().initialize(bot=bot, guild=guild, session=session, **kwargs)
        self.set_roles()
        roles = session.query(db.Role).filter(db.Role.server_id == self.guild_id)
        await self.get_roles(roles)

    async def save_in_database(self, session: Session):
        for group in self.groups:
            for role in self.groups[group]:
                _role: db.Role = await fetch_or_add(db.Role, session, server_id=self.guild_id, id=role)
                if not _role.permissions:
                    _role.permissions = group
                session.merge(_role)

        return await super().save_in_database(session)

    def set_roles(self):
        """Sets roles in cache based on current roles data"""
        for id, role in self.roles.items():
            if role.name == "Voice":
                self.voice_link = id

    async def get_roles(self, roles: Query[db.Role]):
        """Retrieves role settings from Database"""
        permissions = roles.filter(db.Role.permissions).all()
        for role in permissions:
            g = Groups.get(role.permissions)
            if g in self.groups:
                self.groups[g].add(role.id)


class ReactionRoles(Roles):
    reaction_roles: dict[str, dict[Snowflake, dict[str, list[Snowflake]]]]
    """Mapping of Message IDs to Mapping of Reactions to list of Roles to toggle"""

    def __init__(self, *, guild: Guild, **kwargs) -> None:
        self.reaction_roles = {}

        super().__init__(guild=guild, **kwargs)

    async def get_roles(self, roles: Query[db.Role]):
        # NOTE: Rework necessary
        reactions = roles.filter(db.Role.type == "Reaction").all()
        _reactions = {}
        for reaction in reactions:
            if types.Setting.Group in reaction.settings:
                group = reaction.settings[types.Setting.Group].str
            else:
                group = None
            message = reaction.settings[types.Setting.MessageID].snowflake
            _reaction = reaction.settings[types.Setting.Reaction].str
            if group not in _reactions:
                _reactions[group] = {}
            if message not in _reactions[group]:
                _reactions[group][message] = {}
            if reaction not in _reactions[group][message]:
                _reactions[group][message][_reaction] = []
            _reactions[group][message][_reaction].append(reaction.id)
        self.reaction_roles = _reactions
        return await super().get_roles(roles)


class PresenceRoles(Roles):
    presence_roles: dict[str, Snowflake]
    """Mapping of Presence names to Role ID to grant"""

    def __init__(self, *, guild: Guild, **kwargs) -> None:
        self.presence_roles = {}

        super().__init__(guild=guild, **kwargs)

    async def get_roles(self, roles: Query[db.Role]):
        activitites = roles.filter(db.Role.type == "Presence").all()

        for presence in activitites:
            self.presence_roles[presence] = presence.id

        return await super().get_roles(roles)
