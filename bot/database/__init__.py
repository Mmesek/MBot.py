from sqlalchemy.orm import Session, Query # noqa: F401

from MFramework.database.alchemy import Server, Role, Channel, Webhook, Subscription # noqa: F401
from .items import Location, Event, Inventory, Drop, Items # noqa: F401
from .log import Transaction, Activity, Infraction, Log, Statistic, Presence # noqa: F401
from .models import User, Snippet, Task # noqa: F401
from .rp import Skill, Character # noqa: F401
from . import types # noqa: F401

from MFramework import onDispatch
@onDispatch(priority=101)
async def guild_create(bot, guild):
    from ..utils.scheduler import add_guild_tasks
    add_guild_tasks(bot, guild.id)
