import enum
import functools

from MFramework import Allowed_Mentions, Context, Embed, Event, Groups, User, register
from MFramework.commands.cooldowns import CacheCooldown, cooldown

from bot import database as db


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


@register(group=Groups.GLOBAL, main=valentines, private_response=True)
@Event(month=2, day=14)
@cooldown(minutes=10, logic=CacheCooldown)
async def valentine(ctx: Context, user: User, message: str) -> Embed:
    """
    Send a secret valentine to another user!
    Params
    ------
    user:
        User you want to send valentine to
    message:
        Message you want to include in your valentine
    """
    if user.id == ctx.user.id:
        return "You can't send a secret valentine to yourself! :("

    _send(ctx, user, "Secret Valentine")

    await ctx.send(
        f"<@{user.id}>, you have received a valentine!",
        embeds=Embed(title="❤", description=message, color=int("e76f71", 16)),
        allowed_mentions=Allowed_Mentions(users=[user.id]),
        channel_id=ctx.channel_id,
    )

    return "Valentine sent!"


class Valentine(enum.Enum):
    Hug = "Hug"
    Kiss = "Kiss"
    Valentine = "Valentine"


@register(group=Groups.GLOBAL, main=valentines)
@Event(month=2, day=14)
@cooldown(minutes=10, logic=CacheCooldown)
async def send(ctx: Context, user: User, valentine: Valentine) -> Embed:
    """
    Send Hug or kisses to another user!
    Params
    ------
    user:
        User to send to
    valentine:
        Valentine to send
    """
    return _send(ctx, user, valentine)


def _send(ctx: Context, user: User, valentine: Valentine) -> Embed:
    if type(valentine) != str:
        value = valentine.value
    else:
        value = valentine

    if user.id == ctx.user.id:
        return f"You can't send a {value} to yourself! :("

    s = ctx.db.sql.session()

    this_user = db.User.fetch_or_add(s, id=ctx.user_id)
    recipent_user = db.User.fetch_or_add(s, id=user.id)

    inv = db.Inventory(db.items.Item.fetch_or_add(s, name=value, type="Gift"))
    transaction = this_user.transfer(ctx.guild_id, recipent_user, [inv], remove_item=False)

    s.add(transaction)
    s.commit()
    return f"{ctx.user.username} has sent a {value} to <@{user.id}>!"


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
