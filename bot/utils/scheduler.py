import asyncio, datetime

from MFramework import Bot, Snowflake
from .. import database as db

tasks = {}

def scheduledTask(func):
    tasks[func.__name__.lower()] = func
    return func

def add_guild_tasks(self: Bot, guild_id: Snowflake):
    session = self.db.sql.session()
    _tasks = session.query(db.Task).filter(db.Task.server_id == guild_id).filter(db.Task.finished == False).all()
    for task in _tasks:
        _appendTasksToCache(self, task)

def add_task(self: Bot, guild_id: Snowflake, type: db.types.Task, channel_id: Snowflake, message_id: Snowflake, author_id: Snowflake, timestamp: str, finish: bool, prize: str, winner_count: int, finished: bool=False):
    task = db.Task(server_id=guild_id, type=type, channel_id=channel_id, message_id=message_id, user_id=author_id, end=finish, description=prize, count=winner_count, finished=finished)
    self.db.sql.add(task)
    _appendTasksToCache(self, task)

def _appendTasksToCache(self: Bot, task: db.Task):
    cache = self.cache[task.server_id].tasks
    if task.type not in cache:
        cache[task.type] = {}
    cache[task.type][int(task.message_id)] = asyncio.create_task(tasks.get(task.type)(self, task))



async def wait_for_scheduled_task(timestamp: datetime.datetime) -> bool:
    from datetime import datetime, timezone
    delta = (timestamp - datetime.now(tz=timezone.utc)).total_seconds()
    if delta > 0:
        await asyncio.sleep(delta)
    return True
