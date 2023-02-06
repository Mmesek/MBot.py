from datetime import timedelta

from MFramework import Context, Embed, Groups, NotFound, RoleID, User, register

from .. import database as db


@register(group=Groups.NITRO)
async def add(
    ctx: Context,
    type: db.types.Snippet,
    name: str,
    content: str,
    trigger: str = None,
    minimum_group: Groups = Groups.GLOBAL,
    required_role: RoleID = None,
    cooldown: timedelta = None,
    locale: str = None,
) -> str:
    """Adds to or edits existing entry in database
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
        Language of this entry"""
    if not ctx.permission_group.can_use(type.permission):
        return await ctx.reply(f"Sorry, this can be added only by people with `{type.permission.name}` or higher")
    if required_role == ctx.guild_id:
        required_role = None
    snippet = db.Snippet(
        server_id=ctx.guild_id,
        user_id=ctx.user_id,
        role_id=required_role,
        group=minimum_group,
        type=type,
        name=name,
        content=content,
        cooldown=cooldown,
        trigger=trigger,
        locale=locale,
    )
    s = ctx.db.sql.session()
    existing = db.Snippet.filter(s, server_id=ctx.guild_id, user_id=ctx.user_id, name=name, type=type).first()
    ctx.db.sql.merge_or_add(existing, snippet)
    rebuild_cache(ctx, s, type)
    return "Added Succesfully"


@register(group=Groups.NITRO)
async def remove(ctx: Context, type: db.types.Snippet, name: str, *, user: User = None) -> str:
    """
    Removes from database
    Params
    ------
    type:
        type to remove
    name:
        Entry to remove
    user:
        Author that added this snippet. Only Moderators can remove someone elses entry
    """
    if user.id != ctx.user_id and ctx.permission_group.can_use(Groups.MODERATOR):
        return await ctx.reply("Only Moderators and above can remove someone elses entry")
    if not ctx.permission_group.can_use(type.permission):
        return await ctx.reply(f"Sorry, this can be removed only by people with `{type.permission.name}` or higher")
    s = ctx.db.sql.session()
    snippet = db.Snippet.filter(s, server_id=ctx.guild_id, user_id=user.id, name=name, type=type).first()
    if not snippet:
        return await ctx.reply(
            f"Couldn't find anything matching these values: `server = {ctx.guild_id}`, `user = {ctx.user_id}`, `name = {name}`, `type = {type}`"
        )
    s.delete(snippet)
    s.commit()
    ctx.cache.load_from_database(ctx)
    return "Deleted Succesfully"


@register(group=Groups.GLOBAL)
async def stashed(
    ctx: Context,
    type: db.types.Snippet,
    name: str = None,
    search_content: bool = False,
    detailed: bool = False,
    show_all: bool = True,
    *,
    text_only: str = False,
    show_content: str = False,
) -> Embed:
    """
    Stashed snippet to fetch
    Params
    ------
    type:
        type of snippet
    name:
        name of snippet to fetch. Shows all if none provided
    search_content:
        Whether to search contents instead of names
    """
    s = ctx.db.sql.session()
    e = []
    r = db.Snippet.filter(s, server_id=ctx.guild_id, type=type)
    if name and "," in name:
        names = [i.strip() for i in name.split(",")]
    elif name and " " in name:
        names = [i.strip() for i in name.split(" ")]
    else:
        names = [name]
    results = []
    if name and not search_content:
        r = r.filter(db.Snippet.name.in_(names))
    elif name:
        r = r.filter(db.Snippet.content.match(name))
    snippets = r.all()
    results.extend(snippets)
    if detailed:
        embed = Embed()
        desc = []
        for snippet in filter(lambda x: (x.group or Groups.GLOBAL) >= ctx.permission_group, snippets):
            if not name:
                desc.append(f"[<t:{int(snippet.timestamp.timestamp())}:d>] {snippet.name} by <@{snippet.user_id}>")
            else:
                embed.addField(
                    snippet.name,
                    f"` Trigger`: {snippet.trigger}\n` Content`: {snippet.content}\n`   Group`: {snippet.group}\n`Cooldown`: {snippet.cooldown}\n`    Role`: {snippet.role_id}",
                )
        if desc:
            embed.setDescription("\n".join(desc))
        embed.addField("Total", str(len(snippets)))
        return embed
    if results:
        embed = Embed()
        e = sorted(
            [
                i.name if not show_content else i.content
                for i in results
                if not i.group or ctx.permission_group.can_use(i.group)
            ]
        )
        embed.set_description("\n".join(e)).set_footer(f"Total: {len(e)}")
    return embed if not text_only else "\n".join(e)


def rebuild_cache(ctx: Context, s: db.Session = None, type: db.Snippet = None):
    if not s:
        s = ctx.db.sql.session()
    if type is db.types.Snippet.Canned_Response:
        ctx.cache.recompile_Canned(s)
    elif type is db.types.Snippet.Regex:
        ctx.cache.recompile_Triggers(s)
    elif type is db.types.Snippet.Blacklisted_Word:
        ctx.cache.get_Blacklisted_Words(s)
    elif type is db.types.Snippet.Emoji:
        ctx.cache.get_Custom_Emojis(s)
    elif type is db.types.Snippet.Stream:
        ctx.cache.get_tracked_streams(s)
    elif type is db.types.Snippet.DM_Reply:
        ctx.cache.get_dm_replies(s)
    elif type is db.types.Snippet.Forum_Autoreply:
        ctx.cache.get_forum_replies(s)


@register(group=Groups.SYSTEM, interaction=False)
async def add_spotify(ctx: Context, artist: str) -> str:
    """
    Adds new Artist to observed list
    Params
    ------
    artist:
        Artist to add
    """
    from MFramework.api.spotify import Spotify

    s = Spotify(ctx.bot.cfg)
    await s.connect()
    r = await s.search(artist)
    _id = r["artists"]["items"][0]["id"]
    await s.disconnect()
    v = db.Spotify(id=_id, artist=artist, added_by=ctx.user_id)
    ctx.db.sql.add(v)
    return f"Spotify Artist {artist} with ID {_id} added succesfully"


@register(group=Groups.SYSTEM, interaction=False)
async def add_rss(ctx: Context, name: str, url: str, feed_language: str = "en") -> str:
    """Adds new RSS to list"""
    import feedparser
    from mlib.colors import get_main_color, getIfromRGB

    feed = feedparser.parse(url)
    av = feed.get("feed", {}).get("image", {}).get("href", None)
    color = getIfromRGB(get_main_color(av))
    r = db.models.RSS(source=name, url=url, language=feed_language, color=color, last=0, avatar_url=av)
    ctx.db.sql.add(r)
    return "RSS Source added succesfully"
