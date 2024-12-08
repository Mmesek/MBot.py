import asyncio

from MFramework import Bot, Guild, Message, Snowflake, log
from MFramework.cache.base import BasicCache
from sqlalchemy import select

from bot import database as db
from bot.utils.scheduler import tasks as TASK_FUNCTIONS


class Tasks(BasicCache):
    tasks: dict[db.types.Task, dict[Snowflake, asyncio.Task]]
    """Mapping of active tasks like giveaways to their active Task objects"""

    def __init__(self, *, guild: Guild, **kwargs) -> None:
        self.tasks = {}
        super().__init__(guild=guild, **kwargs)

    async def initialize(self, bot: Bot, session: db.Session, guild: Guild, **kwargs) -> None:
        _tasks = await session.query(
            select(db.Task).filter(db.Task.server_id == guild.id, db.Task.finished == False)
        )  # noqa: E712
        if _tasks:
            log.debug("Adding Tasks for guild %s", guild.id)
        for task in _tasks:
            if task.type not in self.tasks:
                self.tasks[task.type] = {}
            log.debug("Adding new %s Task to cache", task.type)
            self.tasks[task.type][task.message_id] = asyncio.create_task(
                TASK_FUNCTIONS[task.type.name.lower()](bot, task)
            )
        return await super().initialize(bot=bot, session=session, guild=guild, **kwargs)


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
