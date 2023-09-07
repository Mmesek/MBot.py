import json
import os
from difflib import get_close_matches
from enum import Enum

import aiohttp
import pycountry
from MFramework import Context, Embed, Groups, Interaction, register
from mlib.colors import get_main_color
from mlib.utils import grouper, truncate

INDEX = {}


class URL(Enum):
    STEAM = "http://api.steampowered.com/"
    STORE = "https://store.steampowered.com/api/"


async def aio_request(path: str = "", query: str = "", method: str = "GET", api: URL = URL.STEAM, **kwargs):
    async with aiohttp.ClientSession() as session:
        request = await session.request(method, api.value + path + query, **kwargs)
        try:
            return await request.json()
        except:
            return request.reason


async def loadAppIndex():
    """Loads Index of Steam Games"""
    if not os.path.exists("data/steamstoreindex.json"):
        await refreshAppIndex()

    global INDEX

    with open("data/steamstoreindex.json") as file:
        INDEX = json.load(file)


async def refreshAppIndex():
    """Updates Index of Steam Games"""
    apps = await aio_request("ISteamApps/GetAppList/v2")
    index = {}
    for each in apps["applist"]["apps"]:
        index[each["name"].lower()] = each["appid"]

    with open("data/steamstoreindex.json", "w", newline="", encoding="utf-8") as file:
        json.dump(index, file, ensure_ascii=False)


async def get_appid(name: str) -> int:
    if not INDEX:
        await loadAppIndex()
    game = get_close_matches(name, INDEX.keys(), 1)[0]
    return INDEX[game]


def country_from_locale(locale: str) -> str:
    code = locale.split("-", 1)
    country = pycountry.countries.get(alpha_2=code[-1])
    language = pycountry.languages.get(alpha_2=code[0])
    return language.name.lower(), country.alpha_2.lower()


async def Game(interaction: Interaction, current: str) -> list[str]:
    if not INDEX:
        await loadAppIndex()
    _index = [i for i in INDEX.keys() if i.strip()]
    matches = get_close_matches(current.lower(), _index, 25)
    if not matches or matches[0] == "":
        matches = list(filter(lambda x: current.title()[:100] in x, _index))[:25]
    return matches


@register(group=Groups.GLOBAL)
async def steam():
    """Fetches data on Steam games"""
    pass


@register(group=Groups.GLOBAL, main=steam)
async def playercount(ctx: Context, game: Game) -> str:
    """
    Fetches playercount for specified game

    Params
    ------
    game:
        Steam game's title.
    """
    appid = await get_appid(game)

    try:
        data = await aio_request("ISteamUserStats/GetNumberOfCurrentPlayers/v1/", f"?appid={appid}")
        count = data.get("response", {}).get("player_count", "Error")
    except KeyError:
        return ctx.t("error", game=game)
    return ctx.t("success", game=game, appid=appid, count=count)


@register(group=Groups.GLOBAL, main=steam)
async def game(ctx: Context, title: Game) -> Embed:
    """
    Shows Steam's game data

    Params
    ------
    title:
        Steam game title.
    """
    appid = await get_appid(title)

    language, country_code = country_from_locale(ctx.language)

    game = await aio_request("appdetails/", f"?appids={appid}&l={language}&cc={country_code}", api=URL.STORE)
    game = game[str(appid)].get("data", {})

    embed = (
        Embed()
        .set_description(game.get("short_description"))
        .set_title(game.get("name"))
        .set_url(f"https://store.steampowered.com/app/{appid}/")
        .set_footer(text=ctx.t("release") + game.get("release_date", {}).get("date", ""))
        .set_image(game.get("header_image", ""))
    )

    prc = game.get("price_overview", {}).get("final_formatted")
    is_free = game.get("is_free", {})
    if prc or is_free:
        if is_free:
            prc = ctx.t("f2p")
        embed.add_field(ctx.t("price"), prc, True)

    r = game.get("recommendations", {}).get("total")
    if r:
        embed.add_field(ctx.t("recommendations"), r, True)

    cp = await aio_request("ISteamUserStats/GetNumberOfCurrentPlayers/v1/", f"?appid={appid}")
    cp = cp.get("response", {}).get("player_count")
    if cp:
        embed.add_field(ctx.t("players"), cp, True)

    ach = game.get("achievements", {}).get("total", 0)
    if ach:
        embed.add_field(ctx.t("achievements"), ach, True)

    required_age = game.get("required_age", 0)
    if required_age:
        embed.add_field(ctx.t("age"), required_age, True)

    dlc = len(game.get("dlc", []))
    if dlc:
        embed.add_field(ctx.t("dlc"), dlc, True)

    f = len(embed.fields)
    if f and f % 3:
        embed.add_field("\u200b", "\u200b", True)

    devs = game.get("developers")
    if devs:
        embed.add_field(ctx.t("developers", count=len(devs)), ", ".join(devs), True)

    publishers = game.get("publishers")
    if publishers and publishers != devs:
        embed.add_field(ctx.t("publishers", count=len(publishers)), ", ".join(publishers), True)

    try:
        await hltb(ctx, game.get("name"), e=embed)
    except:
        pass

    embed.add_field(ctx.t("open"), f"steam://store/{appid}/")
    return embed


class Price:
    def __init__(self, response: dict) -> None:
        self.available = response.get("success", False)
        r = response.get("data", {})
        if not r:
            r = {}
        r = r.get("price_overview", {})
        self.initial = r.get("initial", 0)
        self.final = r.get("final", 0)
        self.currency = r.get("currency", None)


class SteamProfile:
    def __init__(self, steam_id: int, token: str, cc: str) -> None:
        self.country_code = cc
        self.steam_id = steam_id
        self._token = token
        self._prices: dict[int, Price] = {}
        self.games: dict[int, int] = {}

    async def get_games(self):
        r = await aio_request(
            "IPlayerService/GetOwnedGames/v0001/", f"?key={self._token}&steamid={self.steam_id}&format=json"
        )
        self.games = {i["appid"]: i["playtime_forever"] for i in r["response"]["games"]}
        self.total_playtime = sum(list(self.games.values()))
        self.total_hours = truncate(self.total_playtime / 60, 2)
        self.total_played = sum([1 for i in self.games.values() if i > 0])
        self.percent_played = "{:.1%}".format(self.total_played / len(self.games))
        self.hours_per_game = truncate(((self.total_playtime / 60) / self.total_played), 2)

    async def get_prices(self):
        for chunk in grouper(list(self.games.keys()), 100):
            r = await aio_request(
                f"appdetails?appids={','.join([str(i) for i in chunk[:100]])}&filters=price_overview&cc={self.country_code}",
                api=URL.STORE,
            )
            for appid, _game in r.items():
                self._prices[int(appid)] = Price(_game)
        self.total_playtime_with_price = sum(
            [v for k, v in self.games.items() if k in self._prices and self._prices[k].initial > 0]
        )
        self.current_total_prices = sum([i.final for i in self._prices.values()])
        self.has_price = sum([1 for i in self._prices.values() if i.initial])
        self.available = sum([1 for i in self._prices.values() if i.available])
        self.currency = [i.currency for i in self._prices.values() if i.currency][0]
        self.total_price = self.current_total_prices / 100
        self.price_per_hour = "{:.3}".format(truncate(self.total_price / (self.total_playtime_with_price / 60), 2))
        self.price_per_game = "{:.3}".format(truncate(self.total_price / self.has_price), 2)


@register(group=Groups.GLOBAL, main=steam)
async def calculator(ctx: Context, steam_id: str = None, country_code: str = None) -> Embed:
    """
    Steam Calculator. Similiar to Steamdb one (With few differences).

    Params
    ------
    steam_id:
        Your Steam ID or Vanity URL
    country_code:
        Provide Country Code for currency. For example GB for Pounds
    """
    if not steam_id:
        steam_id = ctx.user.username

    token = ctx.bot.cfg.get("Tokens", {}).get("steam", None)
    uid = await aio_request(f"ISteamUser/ResolveVanityURL/v0001/?key={token}&vanityurl={steam_id}")

    try:
        user = uid["response"]["steamid"]
    except KeyError:
        return ctx.t("vanity_url")

    language, country_code = country_from_locale(country_code or ctx.language)

    profile = SteamProfile(user, token=token, cc=country_code)
    try:
        await profile.get_games()
    except KeyError:
        return ctx.t("private_profile")
    await profile.get_prices()

    summary = await aio_request("ISteamUser/GetPlayerSummaries/v2/", f"?key={token}&steamids={user}")
    summary = summary["response"]["players"][0]
    e = (
        Embed()
        .add_field(
            ctx.t("total"),
            ctx.t(
                "total_description",
                playtime=profile.total_hours,
                prices=profile.total_price,
                currency=profile.currency,
            ),
            True,
        )
        .add_field(
            ctx.t("games"),
            ctx.t(
                "games_description",
                game_count=len(profile.games),
                total_played=profile.total_played,
                percent_played=profile.percent_played,
                pricetagged=profile.has_price,
                unavailable=len(profile.games) - profile.available,
                currency=profile.currency,
            ),
            True,
        )
        .add_field(
            ctx.t("average"),
            ctx.t(
                "average_description",
                hours_per_game=profile.hours_per_game,
                price_per_game=profile.price_per_game,
                price_per_hour=profile.price_per_hour,
                currency=profile.currency,
            ),
            True,
        )
        .set_thumbnail(summary["avatarfull"])
        .set_footer(f"SteamID: {user}")
        .set_author(summary["personaname"], summary["profileurl"])
        .set_color(get_main_color(summary["avatar"]))
    )
    return e


@register(group=Groups.GLOBAL, main=steam)
async def hltb(ctx: Context, game: Game, *, e: Embed = None) -> Embed:
    """
    Shows How Long To Beat statistics for provided game

    Params
    ------
    game:
        Game Name
    """
    from howlongtobeatpy import HowLongToBeat

    results = await HowLongToBeat().async_search(game)
    if results is None or len(results) == 0:
        return ctx.t("error")
    g = max(results, key=lambda element: element.similarity)
    if not e:
        e = (
            Embed()
            .set_title(g.game_name)
            .set_url(g.game_web_link)
            .set_thumbnail("https://howlongtobeat.com" + g.game_image_url)
            .set_footer(ctx.t("similiarity", similiarity=g.similarity))
            .set_color(get_main_color("https://howlongtobeat.com" + g.game_image_url))
        )
    e.add_field(g.gameplay_main_label, f"{g.gameplay_main} {g.gameplay_main_unit}", True)
    e.add_field(g.gameplay_main_extra_label, f"{g.gameplay_main_extra} {g.gameplay_main_extra_unit}", True)
    e.add_field(g.gameplay_completionist_label, f"{g.gameplay_completionist} {g.gameplay_completionist_unit}", True)
    return e
