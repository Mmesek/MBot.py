from MFramework import onDispatch
from MFramework.database.alchemy import (  # noqa: F401
    Channel,
    Role,
    Server,
    Subscription,
    Webhook,
)
from sqlalchemy.orm import Query, Session  # noqa: F401

from . import types  # noqa: F401
from .items import Drop, Event, Inventory, Items, Location  # noqa: F401
from .log import Activity, Log, Presence, Statistic, Transaction  # noqa: F401
from .models import Snippet, Task, User  # noqa: F401
from .rp import Character, Skill  # noqa: F401


@onDispatch(priority=101)
async def guild_create(bot, guild):
    from ..utils.scheduler import add_guild_tasks

    add_guild_tasks(bot, guild.id)
