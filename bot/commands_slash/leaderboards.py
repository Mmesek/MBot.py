from MFramework import register, Groups, Event, User, UserID, Embed, Snowflake
from mlib.localization import tr, secondsToText
from MFramework.bot import Context
from ..database import log, types

@register()
async def leaderboard(ctx: Context, *args, language, **kwargs):
    '''Shows leaderboard'''
    pass

@register(group=Groups.GLOBAL, main=leaderboard)
async def exp(ctx: Context, user: User=None):
    '''Shows exp
    Params
    ------
    user:
        if provided, shows exp of specified user, otherwise your own
    '''
    language = ctx.language
    session = ctx.db.sql.session()
    r = log.Statistic.filter(session, server_id=ctx.guild_id, user_id=user.id).all()
    t = ''
    for _t in r:
        if _t.name == types.Statistic.Chat:
            t += tr("commands.exp.chat", language, chat=_t.value)
        elif _t.name == types.Statistic.Voice:
            t += tr("commands.exp.voice", language, voice=secondsToText(_t.value, language.upper()))
    if t == '':
        t = tr("commands.exp.none", language)
    embed = Embed(
        title=f"{user.username}",
        color=ctx.cache.color,
        description=t
    )
    await ctx.reply(embeds=[embed])

from enum import Enum
class TopLeaderboards(Enum):
    Chat = 'chat'
    Voice = 'voice'
    Games = 'games'

@register(group=Groups.GLOBAL, main=leaderboard)
async def top(ctx: Context, limit: int=10, type: TopLeaderboards=None, count: bool=False, activity: bool=False, interval: str='1d', *args, user_id: UserID, language, **kwargs):
    '''Shows leaderboard
    Params
    ------
    limit:
        amount of users to show
    type:
        Type of leaderboard to show. Default is Chat and Voice combined
        Choices:
            Chat = chat
            Voice = voice
            Games = games
    count:
        Whether to show EXP values instead
    activity:
        Whether to show based on recent activity or not
    interval:
        Recent activity period to show. Digits followed by either s, m, h, d or w. For example: 1d 12h 30m 45s
    '''
    await ctx.deferred(False)
    embed = Embed().setColor(ctx.cache.color)
    chat = type is TopLeaderboards.Chat or type is None
    voice = type is TopLeaderboards.Voice
    games = type is TopLeaderboards.Games
    if activity:
        server_messages = ctx.db.influx.get_server(limit, interval, ctx.guild_id, "VoiceSession" if voice else "GamePresence" if games else "MessageActivity", "count" if not voice and not games else "sum")
        if not chat and not voice and not games:
            server_messages += ctx.db.influx.get_server(limit, interval, ctx.guild_id, "VoiceSession", "sum", additional="|> map(fn: (r) => ({r with _value: r._value / 60.0 / 10.0}) )")
        results={}
        for table in server_messages:
            for record in table.records:
                user = record.values.get("user")
                if user not in results:
                    results[user] = 0
                results[user] += record.get_value() or 0
        r = sorted(results, key=lambda i: results[i], reverse=True)
        names = {}
        def get_value(key):
            nonlocal voice, games, language, results, count
            if (voice or games) and not count:
                return secondsToText(int(results[key]), language.upper())
            elif voice and count:
                return int(results[key] / 60 / 10)
            else:
                return int(results[key])
        from MFramework.utils.utils import get_usernames
        for result in r[:limit]:
            names[result] = await get_usernames(ctx.bot, ctx.guild_id, result)
        t = format_leaderboard(r[:limit], user_id, get_name=lambda x: f'`{names.get(x, "Error")}`', get_value=get_value, get_id=lambda x: x)
        embed.setDescription('\n'.join(t) or "No activity detected. It might not be tracked in this server")
        return await ctx.reply(embeds=[embed])
    session = ctx.db.sql.session()
    r = log.Statistic.filter(session, server_id=ctx.guild_id)#.limit(limit).all() #TODO
    if chat:
        r = r.filter_by(name=types.Statistic.Chat)
    elif voice:
        r = r.filter_by(name=types.Statistic.Voice)
    else:
        r = r.filter_by(name=types.Statistic.Game)
    total = r.order_by(log.Statistic.value.desc()).limit(limit).all()
    from MFramework.utils.utils import get_usernames
    names = {}
    for result in total:
        names[result.user_id] = await get_usernames(ctx.bot, ctx.guild_id, result.user_id)
    t = format_leaderboard(total, ctx.user_id, lambda x: f'`{names.get(x.user_id, "Error")}`', lambda x: secondsToText(x.value, language) if voice and not count else x.value, lambda x: x.user_id)
    embed.setDescription('\n'.join(t) or 'None').setColor(ctx.cache.color)
    await ctx.reply(embeds=[embed])

@register(group=Groups.GLOBAL, main=leaderboard)
async def games(ctx: Context, game: str = None, user: UserID = None, reverse=True, *args, language, **kwargs):
    '''Shows users that played specified game or games played by user
    Params
    ------
    game:
        Shows users that played specified game
    user:
        Shows games played by specified user
    reverse:
        Whether to show from most played or not
    '''
    await ctx.deferred(False)
    kw = {}
    if game:
        kw["name"] = game
    if user:
        kw["user_id"] = user
    session = ctx.db.sql.session()
    r = log.Presence.filter(session, server_id=ctx.guild_id, type=types.Statistic.Game, **kw).all()
    embed = Embed()
    d = ''
    if game and not user:
        game = True
        embed.setTitle(tr("commands.games.whoPlayed", language, query=game))
    elif user and not game:
        game = False
        d = tr("commands.games.playedBy", language, query=user)
    else:
        d = tr("commands.games.GameUser", language, game=game, user=user)
    if r != []:
        t = ''
        a = []
        for i in r:
            if game:
                from MFramework.utils.utils import get_usernames
                name = await get_usernames(ctx.bot, ctx.guild_id, i.user_id)
                a += [(name, i.duration)]
            else:
                a += [(i.name, i.duration)]
        a = sorted(a, key=lambda x: x[1], reverse=True)
        t = format_leaderboard(a, ctx.user.username, get_name=lambda x: f'`{x[0]}`', get_value=lambda x: x[1])
    else:
        t = tr("commands.games.none", language)
    if d != '':
        t = d+'\n'.join(t)
    embed.setDescription(t[:2024]).setColor(ctx.cache.color)
    await ctx.reply(embeds=[embed])

class Leaderboards(Enum):
    Easter = 4
    Halloween = 10
    Aoc = 11
    Christmas = 12

#@register(group=Groups.GLOBAL, main=leaderboard)
async def event(ctx: Context, event: Leaderboards, user_id: UserID=None, limit: int=10, *args, language, **kwargs):
    '''
    Shows Event leaderboards
    Params
    ------
    event:
        Which event to show
    user_id:
        Shows stats of another user
    limit:
        How many scores to show
    '''
    s = ctx.db.sql.Session()
    #Eggs found

    #Bites:
    # Vampires
    # Werewolves
    # Zombies
    #Cures:
    # Hunters
    # Huntsmen
    # Enchanters

    #Advent
    #Cookies:
    # Recv
    # Sent
    #Gifts:
    # Recv
    # sent
    #Presents Found

    events = {
        4:["Easter Egg"],
        10:["Vampires", "Werewolves", "Zombies", "Hunters", "Huntsmen", "Enchanters"],
        11:["Top"],
        12:["Advent", "CookiesRecv", "CookiesSent", "GiftsRecv","GiftsSent", "Presents Found"]
    }
    leaderboards = []
    values = []
    for _leaderboard in events[event.value]:
        inventories = prepare_leaderboard(s, _leaderboard, limit)
        leaderboards.append((_leaderboard, inventories))

        user = get_player_stats(s, inventories, ctx.user.id)
        values.append((_leaderboard, user))

    e = Embed().setColor(ctx.cache.color)
    if len(leaderboards) == 1:
        e.setDescription("\n".join(format_leaderboard(inventories, ctx.user.id)))
    else:
        for leaderboard in leaderboards:
            e.addField(leaderboard[0], "\n".join(format_leaderboard(leaderboard[1], ctx.user.id)))
    
    stats = "Your Stats" if not user_id or ctx.user.id == user_id else "Stats"
    e.addField(stats, values) if values else None
    await ctx.reply(embeds=[e])

@Event(month=12)
@register(group=Groups.GLOBAL, interaction=False)#main=leaderboard)
async def aoc(ctx: Context, year:int=None, *args, language, **kwargs):
    '''Shows Advent of Code leaderboard'''
    import requests
    from datetime import datetime
    with open('data/aoc_cookie.txt','r',newline='',encoding='utf-8') as file:
        cookie = file.readline()
    leaderboard_number = 1010436
    r = requests.get(f"https://adventofcode.com/{year or datetime.now().year}/leaderboard/private/view/{leaderboard_number}.json", cookies={"session": cookie})
    r = r.json()
    members = []
    for member in r["members"]:
        members.append({"name": r["members"][member]["name"], "score": r["members"][member]["local_score"], "last_star": r["members"][member]["last_star_ts"], "stars": r["members"][member]["stars"]})
    members = sorted(members, key= lambda i: i["score"], reverse=True)
    t = ["Wynik. Nick - Gwiazdki | Ostatnia\n"]
    for member in members:
        l = f'{member["score"]}. {member["name"]} - {member["stars"]} | {datetime.fromtimestamp(int(member["last_star"])).strftime(" %d/%H:%M").replace(" 0"," ")}'
        if member["name"] == ctx.user.username or member["name"] == ctx.member.nick:
            l = '__' + l + '__'
        if member["stars"] == 0:
            continue
        t.append(l)
    e = (Embed()
        .setFooter("", "1010436-ed148a8d")
        .addField("Uczestników", str(len(members)))
        .setUrl("https://adventofcode.com")
        .setTitle("Advent of Code")
        .setDescription("\n".join(t))
        .setColor(ctx.cache.color)
    )
    await ctx.reply(embeds=[e])

from typing import List
from ..database import items
def format_leaderboard2(ranks: List[items.Inventory], user_id=None):
    rank = []
    for x, rank in enumerate(ranks):
        rank_str = f"{x}. <@{rank.user_id}> - {rank.quantity}"
        if rank.user_id == user_id:
            rank_str = f"__{rank_str}__"
        rank.append(rank_str)
    return rank

def prepare_leaderboard(s, name: str, limit: int=10) -> List[items.Inventory]:
    item = items.Item.by_name(s, name)
    return s.query(items.Inventory).filter(items.Inventory.item_id == item.id).order_by(items.Inventory.quantity.desc()).limit(limit).all() or []

def get_player_stats(s, inventories: List[items.Inventory], user_id: Snowflake) -> str:
    inventory = [i for i in filter(lambda x: x.user_id == user_id, inventories)]
    if inventory == []:
        inventory = s.query(items.Inventory).filter(items.Inventory.item_id == inventories[0].item_id, items.Inventory.user_id == user_id).first()
    return inventory

from typing import Callable

def format_leaderboard(
                    iterable: List[str], 
                    user_id: Snowflake=None, 
                    get_name: Callable = lambda x: f"<@{x.user_id}>", 
                    get_value: Callable = lambda x: x.quantity,
                    get_id: Callable = lambda x: x
                ) -> List[str]:
    _r = []
    for x, rank in enumerate(iterable):
        rank_str = f"{x+1}. {get_name(rank)} - {get_value(rank)}"
        if user_id == get_id(rank):
            rank_str = f"__{rank_str}__"
        _r.append(rank_str)
    return _r 
