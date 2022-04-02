from typing import List, Callable

from MFramework import register, Groups, Event, User, UserID, Embed, Snowflake
from MFramework.bot import Context
from MFramework.utils.leaderboards import Leaderboard, Leaderboard_Entry

from mlib.localization import tr, secondsToText

from ..database import log, types, items

@register()
async def leaderboard(ctx: Context, *args, language, **kwargs):
    '''Shows leaderboard'''
    pass

@register(group=Groups.GLOBAL, main=leaderboard)
async def exp(ctx: Context, user: User=None) -> Embed:
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
    return [Embed(
        title=f"{user.username}",
        color=ctx.cache.color,
        description=str(t)
    )]

from enum import Enum
class TopLeaderboards(Enum):
    Chat = 'chat'
    Voice = 'voice'
    Games = 'games'

@register(group=Groups.GLOBAL, main=leaderboard)
async def top(ctx: Context, limit: int=10, type: TopLeaderboards=None, count: bool=False, activity: bool=False, interval: str='1d') -> Embed:
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
    
    stats = []
    voice = False

    if type is TopLeaderboards.Chat or type is None:
        stats.append(types.Statistic.Chat)
    if type is TopLeaderboards.Voice or type is None:
        if type:
            voice = True
        stats.append(types.Statistic.Voice)
    if type is TopLeaderboards.Games:
        stats.append(types.Statistic.Game)        

    if activity:
        return activity_leaderboard(ctx, limit, interval, voice, count, stats)
    
    session = ctx.db.sql.session()
    from sqlalchemy import func
    q = session.query(func.sum(log.Statistic.value), log.Statistic.user_id)
    r = {}
    for t in stats:
        _ = (q.filter(log.Statistic.name.in_([t]))
            .filter(log.Statistic.server_id == ctx.guild_id)
            .group_by(log.Statistic.user_id)
            .order_by(func.sum(log.Statistic.value).desc())
            .limit(limit * 2)
            .all()
        )
        if (len(stats) > 1 and t is types.Statistic.Voice) and not count:
            _ = [((i[0] // 60 // 10), i[1]) for i in _]
        for value, user in _:
            if user in r:
                r[user] += value
            else:
                r[user] = value

    value_processing = lambda x: secondsToText(x, ctx.language) if voice and not count else x
    r = [Leaderboard_Entry(ctx, k, v, value_processing) for k, v in r.items()]
    r = list(filter(lambda x: x.user_id in ctx.cache.members, r))[:limit]
    r.sort(key=lambda x: x.value, reverse=True)
    r = r[:limit]
    leaderboard = Leaderboard(ctx, ctx.user_id, r, limit)
    return leaderboard.as_embed()

def activity_leaderboard(ctx: Context, limit: int = 10, interval: str='1d', voice: bool = False, count: bool = False, stats = []) -> Embed:
    server_messages = ctx.db.influx.get_server(limit, interval, ctx.guild_id, 
        "VoiceSession" if voice 
        else "GamePresence" if types.Statistic.Game in stats
        else "MessageActivity", 
        "count" if not voice and types.Statistic.Game not in stats
        else "sum"
    ) # This is not like non-activity couterpart as it doesn't mix voice and chat together

    if not stats:
        server_messages += ctx.db.influx.get_server(limit, interval, ctx.guild_id, "VoiceSession", "sum", additional="|> map(fn: (r) => ({r with _value: r._value / 60.0 / 10.0}) )")

    results={}
    for table in server_messages:
        for record in table.records:
            user = record.values.get("user")
            if user not in results:
                results[user] = 0
            results[user] += record.get_value() or 0

    value_processing = lambda x: (
        secondsToText(x, ctx.language) 
        if (voice or types.Statistic.Game in stats) and not count 
        else (x // 60 // 10) if voice and count 
        else x
    )
    results = set(Leaderboard_Entry(ctx, k, v, value_processing) for k, v in results.items())

    leaderboard = Leaderboard(ctx, ctx.user_id, results, limit, error="No activity detected. It might not be tracked in this server")

    return leaderboard.as_embed()

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
    Easter_Egg_2021 = "Easter Egg"
    Easter_Egg = "Easter Egg 2022"
    Pumpkin_Hunt = "Pumpkin"
    #Halloween = "Halloween"
    Fear = "Reinforced Fear"
    Candies = "Halloween Treats"
    Moka = "Moka Treats"
    Present_Hunt = "Presents"
    Sent_Presents = "Sent Present"
    Hitted_Snowballs = "Thrown Snowball"
    Mostly_Snowballed = "Splashed Snowball"
    Grinch = "Stolen Presents"
    Chickens = "Chicken"
    #Cookies = "Cookie"
    #Gifting = "Present"
    #Advent = "Advent"
    #Aoc = 11
    #Christmas = 12

@register(group=Groups.GLOBAL, main=leaderboard)
async def event(ctx: Context, event: Leaderboards, user_id: UserID=None, limit: int=10, year: int=None) -> Embed:
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
    year:
        Leaderboard for which year to show (Default is current year) 
    '''
    s = ctx.db.sql.session()
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

    #events = {
    #    4:["Easter Egg"],
    #    9:["Pumpkin"],
    #    10:["Vampires", "Werewolves", "Zombies", "Hunters", "Huntsmen", "Enchanters"],
    #    11:["Top"],
    #    12:["Advent", "CookiesRecv", "CookiesSent", "GiftsRecv","GiftsSent", "Presents Found"]
    #}    await ctx.deferred(False)


    item = items.Item.by_name(s, event.value)
    # //NOTE: Kinda experimental, when guild is below 1000 members we'll pass to IN current members
    # otherwise we'll get x10 more than limit and attempt to filter them to ones within current guild
    # Whether doing any of this makes any sense is heavly debatable but should do the job
    inventories = s.query(items.Inventory).filter(items.Inventory.item_id == item.id, items.Inventory.quantity > 0)
    og_limit = limit
    if len(ctx.cache.members.keys()) < 1000:
        inventories = inventories.filter(items.Inventory.user_id.in_(list(ctx.cache.members.keys())))
    else:
        limit = limit * 10
    inventories = inventories.order_by(items.Inventory.quantity.desc()).limit(limit).all()
    if og_limit < limit:
        inventories = list(filter(lambda x: x.user_id in ctx.cache.members, inventories))[:og_limit]
    # NOTE//

    if not any(x.user_id == user_id for x in inventories):
        i = s.query(items.Inventory).filter(items.Inventory.item_id == item.id, items.Inventory.user_id == user_id).first()
        if i:
            inventories.append(i)

    r = set(Leaderboard_Entry(ctx, x.user_id, x.quantity) for x in inventories)
    
    leaderboard = Leaderboard(ctx, user_id, r, og_limit)
    return [leaderboard.as_embed(f"{event.value}'s Leaderboard")]

@Event(month=12)
@register(group=Groups.GLOBAL, main=leaderboard, interaction=False)
async def aoc(ctx: Context, year:int=None) -> Embed:
    '''Shows Advent of Code leaderboard'''
    import requests
    import json
    from datetime import datetime
    with open('data/aoc_cookie.txt','r',newline='',encoding='utf-8') as file:
        cookie = file.readline()

    with open('data/aoc_leaderboards.json','r',newline='',encoding='utf-8') as file:
        leaderboards = json.load(file)
    _ = leaderboards.get(str(ctx.guild_id), ({"invite":None, "number":None, "language": ctx.language}))
    leaderboard_number, invite_code, language = _.get("number", None), _.get("invite", ""), _.get("language", ctx.language)
    if not leaderboard_number:
        return "Sorry, there is no leaderboard configured for this server \:("

    r = requests.get(f"https://adventofcode.com/{year or datetime.now().year}/leaderboard/private/view/{leaderboard_number}.json", cookies={"session": cookie})
    r = r.json()
    members = []
    for member in r["members"]:
        members.append({"name": r["members"][member]["name"], "score": r["members"][member]["local_score"], "last_star": r["members"][member]["last_star_ts"], "stars": r["members"][member]["stars"]})
    members = sorted(members, key= lambda i: i["score"], reverse=True)
    t = [tr("commands.aoc.header", language)]

    for member in members:
        l = f'{member["score"]}. {member["name"]} - {member["stars"]} | <t:{member["last_star"]}:t>'
        if member["name"] == ctx.user.username or member["name"] == ctx.member.nick:
            l = '__' + l + '__'
        if member["stars"] == 0:
            continue
        t.append(l)

    return (Embed()
        .setFooter(tr("commands.aoc.participants", language, number=len(members)))
        .setUrl("https://adventofcode.com")
        .setTitle("Advent of Code")
        .setDescription("\n".join(t))
        .addField(tr("commands.aoc.join_title", language), tr("commands.aoc.join_text", language, invite_code=invite_code))
        .setColor(ctx.cache.color)
    )

def prepare_leaderboard(s, name: str, limit: int=10) -> List[items.Inventory]:
    item = items.Item.by_name(s, name)
    return s.query(items.Inventory).filter(items.Inventory.item_id == item.id).order_by(items.Inventory.quantity.desc()).limit(limit).all()

def get_player_stats(s, inventories: List[items.Inventory], user_id: Snowflake) -> str:
    inventory = [i for i in filter(lambda x: x.user_id == user_id, inventories)]
    if inventory == []:
        inventory = s.query(items.Inventory).filter(items.Inventory.item_id == inventories[0].item_id, items.Inventory.user_id == user_id).first()
    return inventory

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

class NoValueEntry(Leaderboard_Entry):
    def __str__(self) -> str:
        return f"`{self.name}`"

class LeaderboardPosition(Leaderboard):
    @property
    def user_stats(self) -> int:
        return f"Estimated Position: ~{self._user_position}"

@register(group=Groups.GLOBAL, main=leaderboard)
async def levels(ctx: Context, limit: int = 10) -> Embed:
    '''Shows levels leaderboard'''
    from ..dispatch.xp import User_Experience
    session = ctx.db.sql.session()
    entries = session.query(User_Experience).filter(User_Experience.server_id == ctx.guild_id).order_by(User_Experience.value.desc()).limit(250).all()
    if not any(ctx.user_id == x.user_id for x in entries):
        u = session.query(User_Experience).filter(User_Experience.server_id == ctx.guild_id, User_Experience.user_id == ctx.user_id).first()
        if u:
            entries.append(u)
    r = set(NoValueEntry(ctx, x.user_id, x.value) for x in entries)
    leaderboard = LeaderboardPosition(ctx, ctx.user_id, r, limit, skip_invalid=True)
    return leaderboard.as_embed()
