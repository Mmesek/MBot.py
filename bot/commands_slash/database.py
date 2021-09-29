from datetime import timedelta
from MFramework import register, Groups, Context, RoleID, User, Embed, NotFound
from .. import database as db

@register(group=Groups.NITRO)
async def add(ctx: Context, 
    type: db.types.Snippet, name: str, content: str, trigger: str=None,
    minimum_group: Groups= Groups.GLOBAL, required_role: RoleID = None, cooldown: timedelta=None, 
    locale: str = None) -> str:
    '''Adds to or edits existing entry in database
    Params
    ------
    type:
        Type of entry to add
    name:
        Name of this entry
    content:
        Response of this entry
    trigger:
        Regular expression
    minimum_group:
        Minimal Permission group that is allowed to use this
    required_role:
        Role that is require to use this
    cooldown:
        Whether this should be executed only once a while
    locale:
        Language of this entry'''
    if not ctx.permission_group.can_use(type.permission):
        return await ctx.reply(f"Sorry, this can be added only by people with `{type.permission.name}` or higher")
    if required_role == ctx.guild_id:
        required_role = None
    snippet = db.Snippet(server_id=ctx.guild_id, user_id=ctx.user_id, role_id=required_role, group=minimum_group, type=type, name=name, content=content, cooldown=cooldown, trigger=trigger, locale=locale)
    s = ctx.db.sql.session()
    existing = db.Snippet.filter(s, server_id=ctx.guild_id, user_id=ctx.user_id, name=name, type=type).first()
    ctx.db.sql.merge_or_add(existing, snippet)
    rebuild_cache(ctx, s)
    return "Added Succesfully"

@register(group=Groups.NITRO)
async def remove(ctx: Context, type: db.types.Snippet, name: str, *, user: User=None) -> str:
    '''
    Removes from database
    Params
    ------
    type:
        type to remove
    name:
        Entry to remove
    user:
        Author that added this snippet. Only Moderators can remove someone elses entry
    '''
    if user.id != ctx.user_id and ctx.permission_group.can_use(Groups.MODERATOR):
        return await ctx.reply("Only Moderators and above can remove someone elses entry")
    if not ctx.permission_group.can_use(type.permission):
        return await ctx.reply(f"Sorry, this can be removed only by people with `{type.permission.name}` or higher")
    s = ctx.db.sql.session()
    snippet = db.Snippet.filter(s, server_id=ctx.guild_id, user_id=user.id, name=name, type=type).first()
    if not snippet:
        return await ctx.reply(f"Couldn't find anything matching these values: `server = {ctx.guild_id}`, `user = {ctx.user_id}`, `name = {name}`, `type = {type}`")
    s.delete(snippet)
    s.commit()
    ctx.cache.load_from_database(ctx)
    return "Deleted Succesfully"

@register(group=Groups.GLOBAL)
async def stashed(ctx: Context, type: db.types.Snippet, name: str=None, search_content: bool=False) -> Embed:
    '''
    Stashed snippet to fetch
    Params
    ------
    type:
        type of snippet
    name:
        name of snippet to fetch. Shows all if none provided
    search_content:
        Whether to search contents instead of names
    '''
    s = ctx.db.sql.session()
    r = db.Snippet.filter(s, server_id=ctx.guild_id, type=type)
    if name and not search_content:
        r = r.filter(db.Snippet.name == name)
    elif name:
        r = r.filter(db.Snippet.content.match(name))
    snippets = r.all()
    embed = Embed()
    desc = []
    for snippet in filter(lambda x: (x.group or Groups.GLOBAL) >= ctx.permission_group, snippets):
        if not name:
            desc.append(f"[<t:{int(snippet.timestamp.timestamp())}:d>] {snippet.name} by <@{snippet.user_id}>")
        else:
            embed.addField(snippet.name, f"` Trigger`: {snippet.trigger}\n` Content`: {snippet.content}\n`   Group`: {snippet.group}\n`Cooldown`: {snippet.cooldown}\n`    Role`: {snippet.role_id}")
    if desc:
        embed.setDescription('\n'.join(desc))
    embed.addField("Total", str(len(snippets)))
    return embed


def rebuild_cache(ctx: Context, s: db.Session=None):
    if not s:
        s = ctx.db.sql.session()
    if type is db.types.Snippet.Canned_Response:
        ctx.cache.recompile_Canned(s)
    elif type in db.types.Snippet.Regex:
        ctx.cache.recompile_Triggers(s)
    elif type is db.types.Snippet.Blacklisted_Word:
        ctx.cache.get_Blacklisted_Words(s)
    elif type is db.types.Snippet.Emoji:
        ctx.cache.get_Custom_Emojis(s)
    elif type is db.types.Snippet.Stream:
        ctx.cache.get_tracked_streams(s)


@register(group=Groups.SYSTEM, interaction=False)
async def add_spotify(ctx: Context, artist: str) -> str:
    '''
    Adds new Artist to observed list
    Params
    ------
    artist:
        Artist to add
    '''
    from MFramework.api.spotify import Spotify
    s = Spotify(ctx.bot.cfg)
    await s.connect()
    r = await s.search(artist)
    _id = r['artists']['items'][0]['id']
    await s.disconnect()
    v = db.Spotify(id=_id, artist=artist, added_by=ctx.user_id)
    ctx.db.sql.add(v)
    return f"Spotify Artist {artist} with ID {_id} added succesfully"

@register(group=Groups.SYSTEM, interaction=False)
async def add_rss(ctx: Context, name: str, url: str, feed_language: str='en') -> str:
    '''Adds new RSS to list'''
    from mlib.colors import get_main_color, getIfromRGB
    import feedparser
    feed = feedparser.parse(url)
    av = feed.get('feed', {}).get('image', {}).get('href', None)
    color = getIfromRGB(get_main_color(av))
    r = db.models.RSS(source=name, url=url, language=feed_language, color=color, last=0, avatar_url=av)
    ctx.db.sql.add(r)
    return "RSS Source added succesfully"

@register(group=Groups.NITRO, guild_only=True)
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
    if emoji and "http" in emoji or ":" in emoji:
        if ':' in emoji and not emoji.startswith("http"):
            emoji_name, id = parseMention(emoji).split(":")
            from mdiscord import CDN_URL, CDN_Endpoints
            emoji = CDN_URL+CDN_Endpoints.Custom_Emoji.value.format(emoji_id=id)
        import requests
        icon = requests.get(emoji)
        if icon.ok:
            from binascii import b2a_base64
            emoji = {"icon":f"data:image/png;base64,{b2a_base64(icon.content).decode()}"}
    else:
        emoji = {"icon": "", "unicode_emoji": emoji}

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

    if not c.get_setting(db.types.Setting.Custom):
        c.add_setting(db.types.Setting.Custom, ctx.user_id)
        s.commit()
    await ctx.reply(f"Role <@&{role.id}> {state} Successfully.\nName: {role.name}\nColor: {role.color}")
    _id, _token = ctx.cache.webhooks.get("nitro_role", (None, None))
    if _id:
        await ctx.bot.execute_webhook(
            webhook_id=_id, 
            webhook_token=_token, 
            content="{user} {state} <@&{role}> with name {name} and color {color}{emoji}".format(
                user=ctx.user.username, state=state, role=role.id, name=role.name, color=role.color, emoji=f" and icon {emoji}" if emoji else ""), 
            username="Nitro Role")
