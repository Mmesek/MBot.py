from MFramework import register, Groups, Context, Interaction, Embed
from MFramework.api.steam import Steam, loadSteamIndex

from mlib.localization import tr

@register(group=Groups.SYSTEM, interaction=False)
async def refreshAppIndex(ctx: Context, *args, data, **kwargs):
    """Updates Index of Steam Games"""
    steamapi = Steam(None)
    apps = await steamapi.AppList()
    index = {}
    for each in apps["applist"]["apps"]:
        index[each["name"]] = each["appid"]
    import json
    with open("data/steamstoreindex.json", "w", newline="", encoding="utf-8") as file:
        json.dump(index, file)


@register(group=Groups.GLOBAL)
async def steam(ctx: Context, interaction: Interaction, *args, language, **kwargs):
    '''Fetches data on games'''
    pass

async def steamParse(ctx: Context, request, language, game):
    from difflib import get_close_matches
    #game = " ".join(game)
    games = game.split(",")
    if not hasattr(ctx.bot, "index"):
        await loadSteamIndex(ctx)
    for game in games:
        try:
            game = get_close_matches(game, ctx.bot.index.keys(), 1)[0]
        except IndexError:
            yield {}, game
        appid = ctx.bot.index[game]
        if request == "playercount":
            playercount = await Steam.CurrentPlayers(appid)
            yield playercount, game
        elif request == "details":
            page = await Steam.appDetails(appid, language)
            yield page[str(appid)].get("data",{"short_description": "There was an error searching for data, perhaps Steam page doesn't exist anymore?", "name":game}), appid

@register(group=Groups.GLOBAL, main=steam)
async def playercount(ctx: Context, game: str, *args, language, **kwargs):
    '''Fetches playercount for specified game
    Params
    ------
    game:
        Steam game's title(s). Separate using comma `,`'''
    result = tr("commands.playercount.for", language)
    async for playercount, game in steamParse(ctx, "playercount", language, *game):
        try:
            playercount = playercount.get("response",{}).get("player_count","Error")
            result += f"{game}: {playercount}\n"
        except KeyError:
            result += f"{game}: "+tr("commands.playercount.error", language)
    return result[:2000]


def getBazarPrice(game):
    from bs4 import BeautifulSoup
    import requests
    bazar = 'https://bazar.lowcygier.pl/?title='
    data = requests.get(bazar+game)
    soup= BeautifulSoup(data.text,'html.parser')
    lis = soup.find('div', id="w0", class_='list-view')
    sel = lis.find_all('div', class_='col-md-7 col-sm-4 col-xs-6 nopadding')
    prc = 0
    for each in sel:
        if (each.find('h4',class_='media-heading').a.text == game):
            prc = each.find('p',class_='prc').text.replace(' zł','zł')
            url = each.find('h4', class_='media-heading').a.attrs['href']
            break
    if prc != 0:
        return f"[{prc}](https://bazar.lowcygier.pl{url})"
    return 0

def getGGDealsLowPrice(game, language):
    from bs4 import BeautifulSoup
    import requests
    if language == 'en':
        language = 'eu'
    gg = f"https://gg.deals/{language}/region/switch/?return=%2Fgame%2F"#f'https://gg.deals/{language}/game/'
    name2= game.replace(' ','-').replace('!','-').replace('?','-').replace("'",'-').replace('.','').replace(':','').replace(',',' ')
    data = requests.get(gg+name2)
    soup= BeautifulSoup(data.text,'html.parser')
    lis = soup.find('div', class_='price-wrap')
    try:
        prc = lis.find('span', class_='numeric').text.replace('~', '').replace(' zł','zł')
        url2 = soup.find('div', class_='list-items').find('a', {'target': '_blank'})['href']
    except:
        prc = 0
    try:
        li = lis.find('div',class_='lowest-recorded price-widget')
        prc2 = li.find('span', class_='numeric').text.replace('~', '').replace(' zł','zł')
    except:
        prc2 = 0
    if prc != 'Free' and prc != 0:
        p1 = f"[{prc}](https://gg.deals{url2})"
    else:
        p1 = 0
    if prc2 != 0:
        p2 = prc2
    else:
        p2 = 0
    return (p1, p2)


@register(group=Groups.GLOBAL, main=steam)
async def game(ctx: Context, interaction: Interaction, game: str, *args, language, **kwargs):
    '''Shows Steam's game data
    Params
    ------
    game:
        Steam game title(s). Separate using comma `,`'''
    await ctx.deferred()
    _game = game
    async for game, appid in steamParse(ctx, "details", language, game):
        embed = Embed()
        embed.setDescription(game.get("short_description")).setTitle(game.get("name"))
        embed.setUrl(f"https://store.steampowered.com/app/{appid}/").setFooter(
            text=tr("commands.game.release", language) + game.get("release_date",{}).get("date","")
        )
        embed.setImage(game.get("header_image",""))
        prc = game.get("price_overview", {}).get("final_formatted")
        is_free = game.get("is_free", {})
        if prc is not None or is_free:
            if is_free:
                prc = tr("commands.game.f2p", language)
            embed.addField(tr("commands.game.price", language), prc, True)
        if language == "pl":
            bazar = getBazarPrice(game.get("name", "Error"))
            if bazar != 0:
                embed.addField(tr("commands.game.BazarPrice", language), bazar, True)
        ggdeals = getGGDealsLowPrice(game.get("name", "Error"), language)
        if ggdeals[0] != 0:
            embed.addField(tr("commands.game.CurrentLowPrice", language), ggdeals[0], True)
        if ggdeals[1] != 0:
            embed.addField(tr("commands.game.HistLowPrice", language), ggdeals[1], True)
        r = game.get("recommendations", {}).get("total")
        if r is not None:
            embed.addField(tr("commands.game.recommendations", language), r, True)
        cp = await Steam.CurrentPlayers(appid)
        cp = cp.get("response", {}).get("player_count")
        if cp is not None:
            embed.addField(tr("commands.game.players", language), cp, True)
        ach = game.get("achievements", {}).get("total",0)
        if ach is not None and ach != 0:
            embed.addField(tr("commands.game.achievements", language), ach, True)
        required_age = game.get("required_age",0)
        if required_age != 0:
            embed.addField(tr("commands.game.age", language), required_age, True)
        dlc = len(game.get("dlc", []))
        if dlc != 0:
            embed.addField(tr("commands.game.dlc", language), dlc, True)
        f = len(embed.fields)
        if f != 0 and f % 3 != 0:
            embed.addField("\u200b", "\u200b", True)
        devs = game.get("developers")
        if devs is not None:
            embed.addField(tr("commands.game.developers", language, count=len(devs)), ", ".join(devs), True)
        publishers = game.get("publishers")
        if publishers != devs:
            embed.addField(tr("commands.game.publishers", language, count=len(publishers)), ", ".join(publishers), True)
        from howlongtobeatpy import HowLongToBeat
        results = await HowLongToBeat().async_search(' '.join(_game))
        if results is not None and len(results) > 0:
            if len(embed.fields) != 0 and len(embed.fields) % 3 != 0:
                while len(embed.fields) % 3 != 0:
                    if len(embed.fields) == 25:
                        break
                    embed.addField("\u200b", "\u200b", True)
            g = max(results, key=lambda element: element.similarity)
            if g.gameplay_main != -1:
                embed.addField(g.gameplay_main_label, f"{g.gameplay_main} {g.gameplay_main_unit}", True)
            if g.gameplay_main_extra != -1:
                embed.addField(g.gameplay_main_extra_label, f"{g.gameplay_main_extra} {g.gameplay_main_extra_unit}", True)
            if g.gameplay_completionist != -1:
                embed.addField(g.gameplay_completionist_label, f"{g.gameplay_completionist} {g.gameplay_completionist_unit}", True)
        embed.addField(tr("commands.game.open", language), f"steam://store/{appid}/")
        return embed


@register(group=Groups.GLOBAL, main=steam)
async def steamcalc(ctx: Context, steam_id: str=None, country: str = "us", *args, language, **kwargs):
    '''Steam Calculator. Similiar to Steamdb one (With few differences). 
    Params
    ------
    steam_id:
        Your Steam ID or Vanity URL
    country:
        Provide Country Code for currency. For example GB for Pounds'''
    await ctx.deferred()
    if not steam_id:
        steam_id = ctx.user.username
    s = Steam(ctx.bot.cfg.get('Tokens', {}).get('steam', None))
    uid = await s.resolveVanityUrl(steam_id)
    if uid != tr('commands.steamcalc.notFound', language):
        uid = uid['response']
    else:
        return tr('commands.steamcalc.vanityURL', language)
    if uid['success'] == 1:
        user = uid['steamid']
    games = await s.OwnedGames(user)
    try:
        games = games.get('response', {'games': {}})
    except:
        return tr('commands.steamcalc.vanityURL', language)
    if games.get('games',{}) == {}:
        return tr('commands.steamcalc.privateProfile', language)
    total_playtime = 0
    total_played = 0
    game_ids = []
    for game in games['games']:
        total_playtime += game['playtime_forever']
        game_ids += [game['appid']]
        if game['playtime_forever'] != 0:
            total_played += 1
    total_price = 0
    has_price = []
    unavailable = 0
    def calcPrice(prices, total_price, has_price):
        keys = list(prices.keys())
        for x, price in enumerate(prices.values()):
            if price['success'] and price['data'] != []:
                total_price += price['data']['price_overview']['final']
                ending = price['data']['price_overview']['currency']  #['final_formatted'].split(',')[-1][2:]
                endings = {
                    'USD': '$',
                    'EUR': '€',
                    'PLN': 'zł',
                    'GBP': '£'
                }
                ending = endings.get(ending, ending)
                has_price += [int(keys[x])]
            elif not price['success']:
                nonlocal unavailable
                unavailable += 1
        return total_price, ending, has_price
    try:
        from mlib.utils import grouper
        for chunk in grouper(game_ids, 100):
            prices = await s.getPrices(chunk, country)
            total_price, ending, has_price = calcPrice(prices, total_price, has_price)
    except Exception as ex:
        ending = ''
        print(ex)
    from mlib.utils import truncate
    total = tr('commands.steamcalc.playtime', language, hours=truncate(total_playtime/60, 2))
    if total_price != 0:
        total += tr('commands.steamcalc.prices', language, prices=f"{total_price/100} {ending}")
    if len(has_price) != 0:
        str_prices = tr('commands.steamcalc.pricetaged', language, price_taged=len(has_price))
    else:
        str_prices = ''
    str_prices += tr('commands.steamcalc.notAvailable', language, unavailable=unavailable)
    e = Embed().addField(tr('commands.steamcalc.total', language), total, True).addField(tr('commands.steamcalc.games', language), tr('commands.steamcalc.games_desc', language, game_count=games['game_count'], total_played=total_played)  + " ({:.1%})".format(total_played / games['game_count']) + str_prices, True)
    pt = 0
    pf = 0
    for game in games['games']:
        if game['appid'] in has_price:
            if game['playtime_forever'] != 0:
                pf += 1
                pt += game['playtime_forever']
    avg = tr('commands.steamcalc.hoursPerGame', language, avg=0)
    if total_playtime != 0:
        hpg = truncate(((total_playtime / 60) / total_played), 2)
        avg = tr('commands.steamcalc.hoursPerGame', language, avg=hpg)
    if total_price != 0:
        avg += tr('commands.steamcalc.pricePerGame', language, price="{:.3}".format(truncate((total_price / 100) / len(has_price)), 2) + f"{ending}")
        if pt != 0:
            avg += tr('commands.steamcalc.pricePerHour', language, price="{:.3}".format(truncate((total_price / 100) / (pt / 60), 2)) + f"{ending}")
    e.setFooter(f"SteamID: {user}").addField(tr('commands.steamcalc.avg', language), avg, True)
    from mlib.colors import get_main_color
    profile = await s.PlayerSummaries(user)
    profile = profile['response']['players'][0]
    e.setThumbnail(profile['avatarfull']).setAuthor(profile["personaname"],profile["profileurl"],"").setColor(get_main_color(profile['avatar']))
    return e


@register(group=Groups.GLOBAL, main=steam)
async def hltb(ctx: Context, game: str) -> Embed:
    '''Shows How Long To Beat statistics for provided game
    Params
    ------
    game:
        Game Name'''
    e = Embed().setTitle(game)
    from howlongtobeatpy import HowLongToBeat
    results = await HowLongToBeat().async_search(game)
    if results is not None and len(results) > 0:
        g = max(results, key=lambda element: element.similarity)
        e.setTitle(g.game_name).setUrl(g.game_web_link).setThumbnail(g.game_image_url)
        e.addField(g.gameplay_main_label, f"{g.gameplay_main} {g.gameplay_main_unit}", True)
        e.addField(g.gameplay_main_extra_label, f"{g.gameplay_main_extra} {g.gameplay_main_extra_unit}", True)
        e.addField(g.gameplay_completionist_label, f"{g.gameplay_completionist} {g.gameplay_completionist_unit}", True)
        from mlib.colors import get_main_color
        e.setFooter("", f"Title Similiarity: {g.similarity}").setColor(get_main_color(g.game_image_url))
    return e
