import aiohttp
from MFramework import Embed, Groups, register

wiki_url = "https://dyinglight.wiki.gg"  # TODO: Dehardcode base url


async def get_json(url: str) -> dict:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            res = await response.json()
    return res


@register(group=Groups.GLOBAL)
async def wiki() -> Embed:
    pass


@register(group=Groups.GLOBAL, main=wiki)
async def get(title: str):
    """
    Retrieves wiki's content
    Params
    ------
    title:
        Title of article to fetch
    """
    res = await get_json(f"{wiki_url}/api.php?action=query&format=json&prop=cirrusdoc%7Ccontributors&titles={title}")

    pages = res["query"]["pages"]
    # TODO: Parse infobox and separate sections

    contributors = [f"[{c['name']}]({wiki_url}/wiki/User:{c['name']})" for c in res["query"]["contributors"]]

    return (
        Embed()
        .set_url(f"{wiki_url}/wiki/{title}")
        .set_title(title)
        .add_field("Contributors", "\n".join(contributors[:25]))
    )


@register(group=Groups.GLOBAL, main=wiki)
async def search(query: str, limit: int = 10) -> Embed:
    """
    Search wiki
    Params
    ------
    query:
        Text you want to search for
    limit:
        Total amount of results to display
    """
    url = f"{wiki_url}/api.php?action=opensearch&format=json&search={query}&namespace=0&limit={limit}&profile=engine_autoselect"
    res = await get_json(url)
    mapped = dict(zip(res[1], res[-1]))

    if len(mapped) == 1:
        return await get(mapped.keys()[0])

    text = []
    for key, value in mapped.items():
        text.append(f"- [{key}]({value})")

    return Embed().set_title(f"Search results for {res[0]}").set_description("\n".join(text))


@register(group=Groups.GLOBAL, main=wiki)
async def statistics() -> Embed:
    """
    Wiki statistics
    """
    res = await get_json(f"{wiki_url}/api.php?action=query&format=json&meta=siteinfo&siprop=statistics")
    e = Embed()

    for k, v in res["query"]["statistics"].items():
        e.add_field(k.title().replace("Active", "Active "), v, True)

    return e
