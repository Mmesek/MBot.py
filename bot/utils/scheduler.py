import asyncio
import datetime

from MFramework import Bot, Snowflake

from bot import database as db

tasks: dict[str, callable] = {}


def scheduledTask(func):
    tasks[func.__name__.lower()] = func
    return func


def add_task(
    self: Bot,
    guild_id: Snowflake,
    type: db.types.Task,
    channel_id: Snowflake,
    message_id: Snowflake,
    author_id: Snowflake,
    timestamp: str,
    finish: bool,
    prize: str,
    winner_count: int,
    finished: bool = False,
):
    task = db.Task(
        server_id=guild_id,
        type=type,
        channel_id=channel_id,
        message_id=message_id,
        user_id=author_id,
        end=finish,
        description=prize,
        count=winner_count,
        finished=finished,
    )
    s = self.db.sql.session()
    channel = db.Channel.fetch_or_add(s, server_id=guild_id, id=channel_id)
    s.add(task)
    s.commit()
    # self.db.sql.add(task)
    _appendTasksToCache(self, task)


def _appendTasksToCache(self: Bot, task: db.Task):
    cache = self.cache[task.server_id].tasks
    if task.type not in cache:
        cache[task.type] = {}
    if int(task.message_id) not in cache[task.type]:
        log.debug("Appending new %s Task to cache", task.type)
        cache[task.type][int(task.message_id)] = asyncio.create_task(tasks.get(task.type.name.lower())(self, task))


async def wait_for_scheduled_task(timestamp: datetime.datetime) -> bool:
    from datetime import datetime, timezone

    delta = (timestamp - datetime.now(tz=timezone.utc)).total_seconds()
    log.debug("Waiting for Task for %ss", delta)
    if delta > 0:
        await asyncio.sleep(delta)
    return True
