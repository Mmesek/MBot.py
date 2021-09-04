from MFramework import onDispatch, Bot, Guild_Member_Update, Snowflake
async def new_booster(ctx: Bot, user_id: Snowflake, guild_id: Snowflake):
    import json
    language = ctx.cache[guild_id].language
    with open(f'../data/nitro_welcome_{language}.json','r',newline='',encoding='utf-8') as file:
        f = json.load(file)
    greeting, color, fine_print, if_interest, ending, note = f["greeting"], f["color"], f["fine_print"], f["if_interest"], f["ending"], f["note"]
    from random import choice
    cmd_line = "`/role` `color: #HexadecimalColor` `name: Name of your role`"
    message = ' '.join([choice(greeting).format(user=user_id), choice(color), choice(fine_print), choice(if_interest).format(bot=ctx.username, cmd=cmd_line), choice(ending), choice(note)])
    await ctx.create_message(ctx.cache[guild_id].nitro_channel, message)

async def end_booster(ctx: Bot, user_id: Snowflake, guild_id: Snowflake):
    from MFramework.database import alchemy as db
    s = ctx.db.sql.session()
    c = db.Role.filter(s, server_id=guild_id).filter(
        db.Role.with_setting(db.types.Setting.Custom, user_id)
    ).first()
    if c:
        await ctx.delete_guild_role(guild_id, c.id, "User is no longer Nitro Boosting server")
        s.delete(c)
        s.commit()

@onDispatch
async def guild_member_update(self: Bot, data: Guild_Member_Update):
    await self.cache[data.guild_id].logging["member_update"](data)
    await self.cache[data.guild_id].logging["muted_change"](data)
    is_boosting = await self.cache[data.guild_id].logging["nitro_change"](data)

    if is_boosting and self.cache[data.guild_id].nitro_channel:
        await new_booster(self, data.user.id, data.guild_id)
    elif is_boosting is False and self.cache[data.guild_id].nitro_channel:
        await end_booster(self, data.user.id, data.guild_id)

    self.cache[data.guild_id].members.update(data)
