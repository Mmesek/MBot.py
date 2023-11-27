import asyncio

from MFramework.cache.base import BasicCache

from MFramework import Guild, Message, Snowflake

from ..database import models as db


class Tasks(BasicCache):
    tasks: dict[db.types.Task, dict[Snowflake, asyncio.Task]]
    """Mapping of active tasks like giveaways to their active Task objects"""

    def __init__(self, *, guild: Guild, **kwargs) -> None:
        self.tasks = {}
        super().__init__(guild=guild, **kwargs)


class Safety(BasicCache):
    last_messages: dict[Snowflake, Message]
    """Mapping of Channel ID to Message"""
    moderators: dict[Snowflake, list[Snowflake]]
    """Mapping of Channels to list of designated moderators"""
    msgs_violating_link_filter: set[Message]
    """Recent Message objects violating link filters"""
    last_violating_user: Snowflake
    """Last violating filter User ID"""
    last_joining_user: Snowflake
    """Last User ID that joined guild"""
    allowed_duplicated_messages: int = 1
    """Allowed repeating messages in a row"""

    def __init__(self, **kwargs) -> None:
        self.last_messages = {}
        self.moderators = {}
        self.msgs_violating_link_filter = set()
        self.last_violating_user = None
        self.last_join = None
        self.allowed_duplicated_messages = None

        super().__init__(**kwargs)


class Modmail(BasicCache):
    threads: dict[Snowflake, Snowflake]
    """Mapping of Thread IDs to their main channels"""
    dm_threads: dict[Snowflake, Snowflake]
    """Mapping of Thread IDs to User IDs"""

    def __init__(self, *, guild: Guild, **kwargs) -> None:
        self.threads = {i.id: i.parent_id for i in guild.threads}
        self.dm_threads = {
            i.id: int(i.name.split("-")[-1].strip()) for i in guild.threads if i.name.split("-")[-1].strip().isdigit()
        }
        super().__init__(guild=guild, **kwargs)
