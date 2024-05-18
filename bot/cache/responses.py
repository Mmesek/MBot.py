import re
from typing import Union

from MFramework import Bot
from MFramework.cache.base import RuntimeCommands, Trigger
from MFramework.cache.guild import GuildCache
from sqlalchemy import select
from sqlalchemy.orm import Session

from bot.cache.database import Database
from bot.database import models as db
from bot.database import types


async def query_snippet(session: Session, guild_id: int, type: types.Snippet) -> list[db.Snippet]:
    return session.scalars(select(db.Snippet).where(db.Snippet.server_id == guild_id, db.Snippet.type == type)).all()


class Responses(Database, GuildCache, RuntimeCommands):
    custom_emojis: dict[str, Union[str, tuple[str, str]]]
    """Mapping of Trigger names to Responses"""
    canned: dict[str, re.Pattern]
    """Mapping of Trigger names to Mapping of Type to Regular Expression"""
    blacklisted_words: re.Pattern = None
    """Regular Expression from blacklisted words"""
    tracked_streams: list[str]
    """List of Stream names to track & Notify of"""
    dm_replies: dict[str, str]
    """Mapping of Trigger names to responses for DMs"""
    forum_replies: dict[str, str]
    """Mapping of Trigger names to responses for Forum tags"""

    def __init__(self, **kwargs):
        self.custom_emojis = {}
        self.tracked_streams = []
        self.canned = {}
        self.dm_replies = {}
        self.forum_replies = {}
        super().__init__(**kwargs)

    async def initialize(self, bot: "Bot", session: Session, **kwargs):
        await super().initialize(bot=bot, session=session, **kwargs)
        await self.recompile_canned(session)
        self.custom_emojis = await self.set_custom_emojis(session)
        self.blacklisted_words = await self.get_blacklisted_words(session)
        self.tracked_streams = await self.get_tracked_streams(session)
        self.dm_replies = await self.get_dm_replies(session)
        self.forum_replies = await self.get_forum_replies(session)

    async def set_custom_emojis(self, session: Session):
        custom_emojis = {}
        for emoji in await query_snippet(session, self.guild_id, types.Snippet.Emoji):
            if not emoji.filename:
                custom_emojis[emoji.name.lower()] = emoji.content
            else:
                custom_emojis[emoji.name.lower()] = (emoji.filename, emoji.image)
        return custom_emojis

    async def recompile_canned(self, session: Session):
        triggers = []
        for snippet in await query_snippet(session, self.guild_id, types.Snippet.Canned_Response):
            triggers.append(Trigger(snippet.group, snippet.name, snippet.trigger, snippet.content, snippet.cooldown))
        self.recompile_triggers(triggers)

    async def get_blacklisted_words(self, session: Session):
        if words := await query_snippet(session, self.guild_id, types.Snippet.Blacklisted_Word):
            return re.compile(r"(?i){}".format("|".join([w.name for w in words])))

    async def get_tracked_streams(self, session: Session) -> list[str]:
        return [i.name for i in await query_snippet(session, self.guild_id, types.Snippet.Stream)]

    async def get_dm_replies(self, session: Session) -> dict[str, str]:
        return {i.name: i.content for i in await query_snippet(session, self.guild_id, types.Snippet.DM_Reply)}

    async def get_forum_replies(self, session: Session) -> dict[str, str]:
        return {i.name: i.content for i in await query_snippet(session, self.guild_id, types.Snippet.Forum_Autoreply)}
