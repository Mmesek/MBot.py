import asyncio
import re
from typing import Dict, List, Optional, Tuple, Union

from MFramework import Guild, Snowflake
from MFramework.database.cache import Cache
from MFramework.database.cache_internal import models as collections

from .database import models as db
from .database import types


class Tasks:
    tasks: Dict[db.types.Task, Dict[Snowflake, asyncio.Task]]

    def __init__(self, *, guild: Guild, **kwargs) -> None:
        self.tasks = {}
        super().__init__(guild=guild, **kwargs)


class Cache(Tasks, Cache):
    custom_emojis: Dict[str, Union[str, Tuple]]
    tracked_streams: List[str]
    canned: Dict[str, re.Pattern]
    responses: Dict[Snowflake, re.Pattern]
    dm_replies: Dict[str, str]
    blacklisted_words: re.Pattern = None

    def __init__(self, bot, guild: Guild, rds: Optional[collections.Redis] = None):
        self.custom_emojis = {}
        self.tracked_streams = []
        self.canned = {}
        self.responses = {}
        self.moderators = {}
        self.msgs_violating_link_filter = set()
        self.last_violating_user = None
        self.last_join = None
        super().__init__(bot=bot, guild=guild, rds=rds)

    def load_from_database(self, ctx):
        with ctx.db.sql.Session.begin() as s:
            self.recompile_Triggers(s)
            self.recompile_Canned(s)
            self.get_Custom_Emojis(s)
            self.get_Blacklisted_Words(s)
            self.get_tracked_streams(s)
            self.get_dm_replies(s)

    def get_Custom_Emojis(self, session):
        s = db.Snippet.filter(session, server_id=self.guild_id, type=types.Snippet.Emoji).all()
        for emoji in s:
            if not emoji.filename:
                self.custom_emojis[emoji.name.lower()] = emoji.content
            else:
                self.custom_emojis[emoji.name.lower()] = (emoji.filename, emoji.image)

    def recompile_Canned(self, session):
        s = db.Snippet.filter(session, server_id=self.guild_id, type=types.Snippet.Canned_Response).all()
        import re

        self.canned = {}
        self.canned["patterns"] = re.compile("|".join([f"(?P<{re.escape(i.name)}>{i.trigger})" for i in s]))
        self.canned["responses"] = {re.escape(i.name): i.content for i in s}

    def recompile_Triggers(self, session):
        responses = {}
        triggers = db.Snippet.filter(session, server_id=self.guild_id, type=types.Snippet.Regex).all()
        self.regex_responses = {}
        for trig in triggers:
            if trig.cooldown:
                self.cooldown_values[trig.name] = trig.cooldown
            self.regex_responses[trig.name] = trig.content
            if trig.group not in responses:
                responses[trig.group] = {}
            if trig.name not in responses[trig.group]:
                responses[trig.group][trig.name] = trig.trigger
            else:
                responses[trig.group] = {trig.name: trig.trigger}
        import re

        for r in responses:
            self.responses[r] = re.compile(
                r"(?:{})".format("|".join("(?P<{}>{})".format(k, f) for k, f in responses[r].items()))
            )

    def get_Blacklisted_Words(self, session):
        words = db.Snippet.filter(session, server_id=self.guild_id, type=types.Snippet.Blacklisted_Word).all()
        if len(words) > 0:
            self.blacklisted_words = re.compile(r"(?i){}".format("|".join(words)))

    def get_tracked_streams(self, session):
        self.tracked_streams = [
            i.name for i in db.Snippet.filter(session, server_id=self.guild_id, type=types.Snippet.Stream).all()
        ]

    def get_dm_replies(self, session):
        self.dm_replies = {
            i.name: i.content
            for i in db.Snippet.filter(session, server_id=self.guild_id, type=types.Snippet.DM_Reply).all()
        }

    def get_forum_replies(self, session):
        self.forum_replies = {
            i.name: i.content
            for i in db.Snippet.filter(session, server_id=self.guild_id, type=types.Snippet.Forum_Autoreply).all()
        }
