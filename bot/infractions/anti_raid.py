from datetime import timedelta

from MFramework import (
    Bot,
    Context,
    Groups,
    Guild_Member_Add,
    Message,
    User,
    onDispatch,
    register,
)

from .internal import kick_user


@onDispatch
async def guild_member_add(self: Bot, data: Guild_Member_Add):
    if data.user.id in getattr(self.cache[data.guild_id], "anti_raid_whitelist", []):
        return
    _last = self.cache[data.guild_id].last_join
    self.cache[data.guild_id].last_join = data.user.id

    if _last and abs(_last.as_date - data.user.id.as_date) < timedelta(days=1):
        await kick_user(self, data.guild_id, data.user.id, "Possible Raid: Account Age")

        try:
            await self.remove_guild_member(data.guild_id, _last, "Possible Raid")
        except:
            pass

        return True


@register(group=Groups.ADMIN)
async def ar_whitelist(ctx: Context, user: User):
    """
    Whitelist user in case of false-positive
    Params
    ------
    user:
        User to whitelist
    """
    if not hasattr(ctx.cache, "anti_raid_whitelist"):
        ctx.cache.anti_raid_whitelist = []
    ctx.cache.anti_raid_whitelist.append(user.id)
    return f"Currently whitelisted: {len(ctx.cache.anti_raid_whitelist)} users"


@onDispatch
async def direct_message_create(self: Bot, data: Message):
    guilds = list(
        filter(
            lambda x: data.author.id in x.members,
            [
                cache
                for cache in self.cache.values()
                if type(cache) is not dict and cache.logging.get("direct_message", None)
            ],
        )
    )

    guild_id = guilds[0].guild_id if len(guilds) == 1 else self.primary_guild

    hijacked = {"heyy ummm idk what happened", "find this life-changing"}

    if any(i in data.content for i in hijacked):
        await kick_user(self, guild_id, data.author.id, "Possible Raid: Modmail")

        return True
