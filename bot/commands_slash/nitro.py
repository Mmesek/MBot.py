from MFramework import register, Groups, Context, NotFound
from .. import database as db

@register(group=Groups.NITRO, guild_only=True, private_response=True)
async def nitro(ctx: Context, hex_color: str=None, name: str=None, emoji: str = None) -> str:
    '''
    Create self role. Only one per booster
    Params
    ------
    hex_color:
        Value in hexadecimal notation. For example: #00aaff
    name:
        Name of role
    emoji:
        Icon for this role. Can be Emoji or a link to picture'''
    await ctx.deferred(private=True)
    reserved_colors = set()
    reserved_names = set()
    nitro_position = 0
    
    groups = ctx.cache.groups
    for _role in ctx.cache.roles.values():
        if any(_role.id in groups[i] for i in {Groups.ADMIN, Groups.MODERATOR, Groups.HELPER, Groups.SUPPORT}):
            reserved_colors.add(_role.color)
            reserved_names.add(_role.name.lower())
        elif _role.id in groups[Groups.NITRO]:
            nitro_position = _role.position

    if hex_color:
        try:
            color = int(hex_color.strip('#'), 16)
        except ValueError as ex:
            return "Color has to be provided as a hexadecimal value (between 0 to F for example `#012DEF`) not `"+ str(ex).split(": '")[-1].replace("'","`")
    else:
        color=None

    if color in reserved_colors:
        return "Color is too similiar to admin colors"
    if name and name.lower() in reserved_names:
        return "Sorry, choose different name"

    s = ctx.db.sql.session()
    _roles = db.Role.filter(s, server_id=ctx.guild_id)
    c = _roles.filter(
        db.Role.with_setting(db.types.Setting.Custom, ctx.user_id)
    ).first()
    total_roles = len(_roles.filter(db.Role.settings.any(name=db.types.Setting.Custom)).all())

    if not name:
        if c:
            _r = ctx.cache.roles.get(c.id)
            if _r:
                name = _r.name
            else:
                name = "Nitro Booster"
        else:
            name = "Nitro Booster"
    if '(Nitro Booster)' not in name:
        name += ' (Nitro Booster)'
    
    from MFramework.utils.utils import parseMention
    from mdiscord import CDN_URL, CDN_Endpoints
    if emoji and ("http" in emoji or ":" in emoji):
        if ':' in emoji and not emoji.startswith("http"):
            emoji_name, id = parseMention(emoji).split(":")
            emoji = CDN_URL+CDN_Endpoints.Custom_Emoji.value.format(emoji_id=id)
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get(emoji) as icon:
                if icon.ok:
                    from binascii import b2a_base64
                    emoji = {"icon":f"data:image/png;base64,{b2a_base64(icon.content).decode()}"}
    else:
        emoji = {"icon": "" if emoji else None, "unicode_emoji": emoji}

    if c:
        try:
            role = await ctx.bot.modify_guild_role(ctx.guild_id, c.id, name, 0, color=color, reason="Updated Role of Nitro user", **emoji)
            ctx.cache.roles.update(role)
            state = "updated"
        except NotFound:
            s.delete(c)
            c = None
    if c and role and role.id != c.id or not c:
        if not c and total_roles >= 20:#ctx.cache.settings.get(db.types.Setting.Limit_Nitro_Roles, 20):
            return f"Sorry, limit ({total_roles}) of custom roles has been reached :("
        role = await ctx.bot.create_guild_role(ctx.guild_id, name, 0, color, False, mentionable=False, reason="Created Role for Nitro user "+ctx.member.user.username, **emoji)
        await ctx.bot.modify_guild_role_positions(ctx.guild_id, role.id, nitro_position+1)
        await ctx.bot.add_guild_member_role(ctx.guild_id, ctx.member.user.id, role.id, "Nitro role")
        c = db.Role.fetch_or_add(s, server_id=ctx.guild_id, id=role.id)
        ctx.cache.roles.store(role)
        state = "created"
    
    emoji = (CDN_URL+CDN_Endpoints.Role_Icon.value.format(role_id=role.id, role_icon=role.icon)) if role.icon else role.unicode_emoji if role.unicode_emoji else None

    if not c.get_setting(db.types.Setting.Custom):
        c.add_setting(db.types.Setting.Custom, ctx.user_id)
        s.commit()
    await ctx.reply(f"Role <@&{role.id}> {state} Successfully.\nName: {role.name}\nColor: {role.color}\nIcon: {emoji}")
    _id, _token = ctx.cache.webhooks.get("nitro_role", (None, None))
    if _id:
        await ctx.bot.execute_webhook(
            webhook_id=_id, 
            webhook_token=_token, 
            content="{user} {state} <@&{role}> with name {name} and color {color}{emoji}".format(
                user=ctx.user.username, state=state, role=role.id, name=role.name, color=role.color, emoji=f" and icon {emoji}" if emoji else ""), 
            username="Nitro Role")

@register(group=Groups.ADMIN, interaction=False)
async def remove_invalid(ctx: Context):
    '''
    Clears invalid roles from DB
    '''
    s = ctx.db.sql.session()
    from MFramework.database.alchemy.models import Role
    roles = s.query(Role).filter(Role.server_id == ctx.guild_id).all()
    server_roles = [r for r in ctx.cache.roles]
    to_delete = []
    for role in roles:
        if role.id not in server_roles:
            s.delete(role)
            to_delete.append(role.id)
    s.commit()
    return ", ".join([f"<@&{id}>" for id in to_delete])

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

@onDispatch(priority=90)
async def guild_member_update(self: Bot, data: Guild_Member_Update):
    await self.cache[data.guild_id].logging["muted_change"](data)
    is_boosting = await self.cache[data.guild_id].logging["nitro_change"](data)

    if is_boosting and self.cache[data.guild_id].nitro_channel:
        await new_booster(self, data.user.id, data.guild_id)
    elif is_boosting is False and self.cache[data.guild_id].nitro_channel:
        await end_booster(self, data.user.id, data.guild_id)
