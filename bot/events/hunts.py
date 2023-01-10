import asyncio
import functools
from datetime import datetime
from random import SystemRandom

random = SystemRandom()

import sqlalchemy as sa
from mdiscord import (
    Allowed_Mention_Types,
    Allowed_Mentions,
    Message,
    Message_Reaction_Add,
    onDispatch,
)
from MFramework import (
    Bot,
    Chance,
    Context,
    Cooldown,
    EventBetween,
    Groups,
    log,
    register,
)

from ..database import items, types


class Hunts:
    server_id = sa.Column(sa.ForeignKey("Server.id"))
    start = sa.Column(sa.DateTime)
    end = sa.Column(sa.DateTime)
    item_id = sa.Column(sa.ForeignKey("Item.id"))
    item: items.Item = sa.orm.relationship("Item")
    min_quantity = sa.Column(sa.Integer)
    max_quantity = sa.Column(sa.Integer)
    delete_own = sa.Column(sa.Boolean)
    min_participants = sa.Column(sa.Integer)
    max_participants = sa.Column(sa.Integer)
    loterry = sa.Column(sa.Boolean)
    required_item_id = sa.Column(sa.ForeignKey("Item.id"))
    required_min_quantity = sa.Column(sa.Integer)
    required_max_quantity = sa.Column(sa.Integer)
    min_delay = sa.Column(sa.Integer)
    max_delay = sa.Column(sa.Integer)
    min_wait = sa.Column(sa.Integer)
    max_wait = sa.Column(sa.Integer)
    cleanup = sa.Column(sa.Boolean)
    cleanup_after = sa.Column(sa.Integer)
    require_recent_activity = sa.Column(sa.Integer)
    logger = sa.Column(sa.String)
    announce = sa.Column(sa.Boolean)


async def handle_drop(
    ctx: Bot,
    data: Message,
    reaction: str,
    name: str,
    instance_id: int,
    min_quantity: float = 1,
    max_quantity: float = 1,
    delete_own: bool = True,
    max_participants: int = 0,
    lottery: bool = False,
    active_in_last_msgs: int = None,
    logger: str = None,
    announce_msg: bool = False,
    require_instance_id: int = None,
    require_min_quantity: float = 1,
    require_max_quantity: float = 1,
    quantity_exchange_ratio: float = 1,
    min_initial_delay: int = 0,
    max_initial_delay: int = 10,
    min_wait: int = 15,
    max_wait: int = 60,
    cleanup: bool = False,
    cleanup_after: int = 60,
):
    """
    Main Hunt event logic

    Parameters
    ----------
    reaction:
    name:
    min_quantity:
    max_quantity:
    delete_own:
    max_participants:
    lottery:
    active_in_last_msgs:
    logger:
    announce_msg:
    require:
    require_min_quantity:
    require_max_quantity:
    quantity_exchange_ratio:
    min_initial_delay:
    max_initial_delay:
    min_wait:
    max_wait:
    cleanup:
    cleanup_after:
    """
    log.debug("Spawning reaction with %s", name)

    await data.typing()
    await asyncio.sleep(random.randint(min_initial_delay, max_initial_delay))
    await data.react(reaction)

    quantity = random.randint(min_quantity, max_quantity)
    if quantity_exchange_ratio:
        require_quantity = quantity * quantity_exchange_ratio
    else:
        require_quantity = random.randint(require_min_quantity, require_max_quantity)

    sleep = random.randint(min_wait, max_wait)

    if max_participants == 1 and not lottery:

        def first_only_predicate(x: Message_Reaction_Add) -> bool:
            if (
                x.channel_id == data.channel_id
                and x.message_id == data.id
                and x.user_id != ctx.user_id
                and x.emoji.name == reaction.split(":")[0]
                # TODO Check here if user sent message within last x messages
            ):
                return True
            return False

        try:
            user = await ctx.wait_for("message_reaction_add", check=first_only_predicate, timeout=sleep)
            users = [user.user_id]
        except asyncio.TimeoutError:
            log.debug("No one reacted. Removing reaction")
            return await data.delete_reaction(reaction)
    else:
        await asyncio.sleep(sleep)
        users = [i.id for i in await data.get_reactions(reaction)]

    if active_in_last_msgs:
        # TODO: Get from cache, check if users were active
        pass

    if max_participants and lottery:
        users = random.choices(users, k=max_participants)

    if delete_own or cleanup:
        await data.delete_reaction(reaction)

    if not users:
        return

    users = users[: max_participants or None]
    _claimed_by = await ctx.db.supabase.rpc(
        "add_item",
        server_id=data.guild_id,
        user_ids=users,
        instance_id=instance_id,
        quantity=quantity,
        required_instance_id=require_instance_id,
        required_quantity=require_quantity,
    )
    _not_enough = [user for user in users if user not in _claimed_by]

    await ctx.cache[data.guild_id].logging[logger](data, users)

    result = ""

    if announce_msg:
        if not _claimed_by and _not_enough:
            users_not_claimed = ", ".join([f"<@{i}>" for i in _not_enough])
        users_claimed = ", ".join([f"<@{i}>" for i in _claimed_by])
        # TODO: Finish formatting message!

        if quantity > 1:
            pass
            # result += f" x {quantity}"
        if require_instance_id:
            pass
            # result += f" for {required_item.emoji} {required_item.name}"
            if require_quantity > 1:
                pass
                # result += f" x {require_quantity}"

        msg = await data.reply(result, allowed_mentions=Allowed_Mentions(parse=[Allowed_Mention_Types.User_Mentions]))

    if cleanup:
        await asyncio.sleep(cleanup_after)
        await ctx.delete_all_reactions_for_emoji(data.channel_id, data.id, emoji=reaction, reason="Cleanup")
        await msg.delete(reason="Cleanup")


async def get_hunts(ctx: Bot):
    # TODO: Get Hunts from Database and set them up here!
    s = ctx.db.sql.session
    hunts = s.query(Hunts).all()
    # hunts = []
    for hunt in hunts:
        # TODO: Add support for total reactions/claims possible
        handler = functools.partial(
            handle_drop,
            reaction=hunt.item.emoji,
            name=hunt.item.name,
            quantity=hunt.min_quantity,
            delete_own=hunt.delete_own,
            max_participants=hunt.max_participants,
            lottery=hunt.lottery,
            logger=hunt.logger,
            announce_msg=hunt.announce,
            require=hunt.required_item_id,
            require_quantity=hunt.required_min_quantity,
            min_initial_delay=hunt.min_delay,
            max_initial_delay=hunt.max_delay,
            min_wait=hunt.min_wait,
            max_wait=hunt.max_wait,
            cleanup=hunt.cleanup,
            cleanup_after=hunt.cleanup_after,
            active_in_last_msgs=hunt.require_recent_activity,
        )
        from MFramework.commands.decorators import InGuild

        def before_execution(**kwargs):
            quantity = random.randint(hunt.min_quantity, hunt.max_quantity)
            required_quantity = random.randint(hunt.required_min_quantity, hunt.required_max_quantity)
            # FIXME: Run pre-execution randomizations?
            return handler(**kwargs)

        handler = before_execution

        handler = Chance(hunt.chance)(handler)
        if hunt.cooldown:
            handler = Cooldown(delta=hunt.cooldown)(handler)
        handler = EventBetween(after_timestamp=hunt.start, before_timestamp=hunt.end)(handler)
        if hunt.guild_id:
            handler = InGuild(hunt.guild_id)(handler)
        onDispatch(f=handler, priority=200, event="message_create")


@register(group=Groups.ADMIN)
async def hunt():
    """Base command for managing hunts"""
    pass


@register(group=Groups.ADMIN, main=hunt)
async def create(
    ctx: Context,
    name: str,
    description: str,
    start_date: datetime,
    end_date: datetime,
    reactions: str,
    item_name: str,
    quantity: str = 1,
    require_item: str = None,
    require_quantity: str = 0,
    exchange_ratio: float = 1,
    max_winners: int = 1,
    lottery: bool = False,
    active_within: int = None,
    repeating: bool = True,
):
    """
    Allows creating new Hunts
    Params
    ------
    name:
        Name of the hunt
    description:
        Description of the hunt
    start_date:
        When should hunt start
    end_date:
        When should hunt end
    repeating:
        Whether this hunt should be repeating
    reactions:
        List (comma separated) of possible reactions in this hunt
    item_name:
        Name of an item that should be given to person that reacted
    quantity:
        Amount of items that should be given. For range specify min and max value
    require_item:
        Item required and removed upon upon reacting
    require_quantity:
        Amount of items needed in order to claim. For range specify min and max value
    exchange_ratio:
        Ratio of Required to Received items. Set to 0 for random
    max_winners:
        Limit of winners per each drop. Set to 0 for no limit
    lottery:
        Whether all or random should receive reward (Depending on max_winners)
    active_within:
        Amount of last messages in a channel in which user should be present to be eligible
    """
    pass


# Month  | Chance | Item             | First Only | Quantity | Required Quantity
# 4      | 2.5%   | Easter Egg       | False
# 10     | 1%     | Pumpkin          | True
# 10     | 1.5%   | Halloween Treats | False      | 1-5
# 10     | 3%     | Fear             | True       | 10-32    | 1-5
# 11.05  | 7%     | Moka Treats      | True a:mokaFoil:905061222846697503 / a:petmoka:856587425043578900
# 12     | 3%     | Present          | True
# 12     | 10     | Snowball         | True
