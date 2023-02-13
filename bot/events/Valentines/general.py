import enum
import functools

from MFramework import Context, Embed, Event, Groups, User, register
from MFramework.commands.cooldowns import CacheCooldown, cooldown


def _t(key, language="en", **kwargs):
    from mlib.localization import tr

    return tr("bot.events.Valentines.translations." + key, "en-US", **kwargs)


def inner(f, main: object, should_register: bool = True):
    @functools.wraps(f)
    def wrapped(**kwargs):
        return f(**kwargs)

    if should_register:
        register(group=Groups.GLOBAL, main=main)(Event(month=2, day=14)(wrapped))
    return wrapped


@register(group=Groups.GLOBAL)
def valentines(cls=None, *, should_register: bool = True):
    """Valentine Event commands"""
    i = functools.partial(inner, main=valentines, should_register=should_register)
    if cls:
        return i(cls)
    return i


def compatibility(user_id_a, user_id_b) -> float:
    import random

    random.seed(user_id_a + user_id_b)
    return random.random() * 100


@valentines
async def lovemeter(ctx: Context, user: User) -> str:
    """
    Shows the meter of how compatible you are with another user
    Params
    ------
    user:
        User to compare with
    """
    value = compatibility(ctx.user_id, user.id)
    return f"`[{'#'*int(value//10):.<10}]` {value:.3}%"
