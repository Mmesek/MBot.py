from MFramework import register, Groups, Embed, Context
import requests

@register(group=Groups.GLOBAL)
async def search(ctx: Context):
    '''Searches things'''
    pass

@register(group=Groups.GLOBAL, main=search, interaction=False)
async def api(ctx: Context, category: str, random: bool=False, desc: str='', title: str='', cors: str='', https: bool=True, auth: str='') -> Embed:
    '''Search for API
    Params
    ------
    category:
        Category of an API
    random:
        Whether Should fetch random API
    desc:
        Description of API
    title:
        Title of API
    cors:
        Cross Origin Reasource Sharing
    https:
        Whether API should support HTTPS
    auth:
        Authorization method'''
    #Inspired by https://github.com/Vik0105/Devscord
    base_url = "https://api.publicapis.org/"
    params = []
    if category != ():
        params += ["category=" + category]
    if desc:
        params += ["description=" + desc]
    if title:
        params += ["title=" + title]
    if cors in ['yes','no','unknown']:
        params += ["cors=" + cors]
    if https in ["true", "false"]:
        params += ["https=" + https]
    if auth:
        params += ["auth="+auth]

    if random:
        url = base_url + "random"
        url += '?' + '&'.join(params)
        r = requests.get(url)
        response = r.json()['entries'][0]
        e = Embed().setTitle(response['API']).setDescription(response["Description"])
        e.addField("HTTPS", f'{response["HTTPS"]}', True).addField("Category", response["Category"], True).addField("Cross-Origin Resource Sharing", response["Cors"], True).addField("URL", response["Link"], True)
        if response['Auth'] != "":
            e.addField("Auth", response["Auth"], True)
        return e
    if params == [] and category == ():
        r = requests.get(base_url + "categories")
        categories = ', '.join(r.json())
        return "Available categories: " + categories
    url = base_url + "entries"
    url += '?' + '&'.join(params)
    r = requests.get(url)
    apis = ''
    response = r.json()
    embed = Embed().setTitle(category).setFooter("", f"Total: {response['count']}")
    for api in response['entries']:
        title = api["API"]
        _ = f'- {api["Description"]}\n{api["Link"]}'
        if response['count'] < 25:
            embed.addField(title, _, True)
        else:
            _ = f"**{title}**\n{_}\n"
            if len(apis + _) < 2000:
                apis += _
            else:
                break
    if apis != '':
        embed.setDescription(apis)
    return embed

@register(group=Groups.GLOBAL, main=search, interaction=False)
async def stack(ctx: Context, search: str) -> Embed:
    '''Search Stack Overflow
    search:
        Query to search'''
    #Inspired by https://github.com/Vik0105/Devscord
    r = requests.get("https://api.stackexchange.com/2.2/search?order=desc&site=stackoverflow&intitle=" + search)
    r = r.json()
    size = f'Total Questions: {len(r["items"])}'
    if r["has_more"]:
        size+= "+"
    e = Embed().setTitle(search).setFooter(size)
    desc = ''
    for q in r['items']:
        question = f'- [{q["title"]}]({q["link"]})\nTags: {", ".join(q["tags"])}'
        answered = q["is_answered"]
        if answered:
            question = "☑️" + question
        else:
            question = "❌" + question
        question += f'\nAnswers/Views: {q["answer_count"]}/{q["view_count"]}\n'
        if len(r['items']) < 25:
            e.addField(q["title"], question, True)
        else:
            if len(desc + question) < 2000:
                desc += question
            else:
                break
        if desc != '':
            e.setDescription(desc)
    return e

@register(group=Groups.GLOBAL, main=search, interaction=False)
async def spotify(ctx: Context, query: str) -> Embed:
    '''Search Spotify
    Params
    ------
    query:
        Artist to search for'''
    from MFramework.api.spotify import Spotify
    s = Spotify(ctx.bot.cfg)
    await s.connect()
    res = await s.search(query.replace('_','+'), 'artist', '&limit=10')
    l = ''
    for i in res['artists']['items']:
        l += f"\n- [{i['name']}](https://open.spotify.com/artist/{i['id']})"
    embed = Embed().setDescription(l).setColor(1947988).setAuthor(query,res['artists']['href'].replace('api','open').replace('/v1/','/').replace('?query=','/').split('&')[0],'https://images-eu.ssl-images-amazon.com/images/I/51rttY7a%2B9L.png').setThumbnail(res['artists']['items'][0]['images'][0]['url'])
    await s.disconnect()
    return embed

@register(group=Groups.GLOBAL, main=search)
async def urban(ctx: Context, phrase: str) -> Embed:
    '''
    Searches Urban Dictionary for provided phrase
    Params
    ------
    phrase:
        Phrase to search definition of
    '''
    await ctx.deferred()
    url = "http://api.urbandictionary.com/v0/define?term="+phrase
    r = requests.get(url)
    try:
        r = r.json()['list'][0]
    except IndexError:
        return "Error occured. No results found."
    e = (Embed()
        .setTitle(r["word"])
        .setDescription(r["definition"])
        .setUrl(r["permalink"])
        .addField("Examples", r.get("example", None) or "...")
        .addField("👍", str(r.get("thumbs_up", 0)), inline=True)
        .addField("👎", str(r.get("thumbs_down", 0)), inline=True)
        .setFooter(f"by {r.get('author', 'Anonymous')}")
        .setTimestamp(r["written_on"])
        .setColor(1975351)
    )
    return e

@register(group=Groups.GLOBAL, main=search, interaction=False)
async def fileext(ctx: Context, ext: str) -> Embed:
    '''Shows file extension details
    Params
    ------
    ext:
        File Extension to search for'''
    from bs4 import BeautifulSoup
    url = f"https://fileinfo.com/extension/{ext}"
    r = requests.get(url)
    if r.status_code == 200:
        soup = BeautifulSoup(r.content, "html.parser")
    else:
        return "Error"
    article = soup.find('article')
    header = article.find('h1').text
    ftype = article.find('h2').text.replace('File Type','')
    misc = article.find('div', class_='fileHeader').find('table').find_all('tr')
    info = article.find('div', class_='infoBox').text
    e = Embed().setTitle(header).addField('File Type', ftype, True).setDescription(info).setUrl(url)
    for i in misc:
        if 'developer' in i.text.lower():
            e.addField('Developer', i.text[9:], True)
        elif 'category' in i.text.lower():
            e.addField('Category', i.text[8:], True)
        elif 'format' in i.text.lower():
            e.addField('Format', i.text[6:], True)
    return e

@register(group=Groups.SYSTEM, main=search, interaction=False)
async def google(ctx: Context, query: str) -> Embed:
    '''Searches google
    Params
    ------
    query:
        Query to search'''
    query = "".join(query).replace(" ", "+")
    language = "en"
    limit = 4
    resp = requests.get(
        f"https://google.com/search?q=how+{query}&hl={language}&gl={language}",
        headers={"user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:65.0) Gecko/20100101 Firefox/65.0"},
    )
    results = []
    from bs4 import BeautifulSoup
    if resp.status_code == 200:
        soup = BeautifulSoup(resp.content, "html.parser")
    else:
        return "Error"
    for x, g in enumerate(soup.find_all("div", class_="r")):
        anchors = g.find_all("a")
        if anchors:
            link = anchors[0]["href"]
            title = g.find("h3").text
            item = {"title": title, "link": link}
            results.append(item)
    for x, s in enumerate(soup.find_all("div", class_="s")):
        desc = s.find("span", class_="st").text
        results[x]["description"] = desc

    embed = Embed()
    for x, result in enumerate(results):
        embed.addField(result["title"], f"[Link]({result['link']})\n{result['description'][:900]}")
        if x == limit:
            break
    return embed

async def azlyrics(artist, song):
    from bs4 import BeautifulSoup
    song = song.replace('-','').replace(' ','').replace('the','').casefold()
    artist = artist.replace('-','').replace(' ','').replace('the','').casefold()
    url = f'https://www.azlyrics.com/lyrics/{song}/{artist}.html'
    req = requests.get(url)
    soup = BeautifulSoup(req.text,'html.parser')
    lyric = soup.find('div',class_='container main-page').find('div',class_="col-xs-12 col-lg-8 text-center").find('div', class_=None).text
    lyric = lyric.replace('\r',"")
    lyric1 = lyric.split("\n\n")
    try:
        embed = Embed().addFields(f'{song} - {artist}', lyric)
    except:
        return '404'
    return embed

async def glyrics(artist, song):
    song1 = (artist.lower(), song.lower())
    from bs4 import BeautifulSoup
    req = requests.get(f'https://genius.com/{song1[0]}-{song1[1]}-lyrics')
    song1[1] = song1[1].replace('-',' ').capitalize()
    song1[0] = song1[0].replace('-',' ').capitalize()
    song = f'{song1[0]} - {song1[1]}'
    soup = BeautifulSoup(req.text,'html.parser')
    lyric = soup.find('div',class_='lyrics').text
    lyric = lyric.replace('\r',"").replace('"','')
    lyric1 = lyric.split("\n\n")
    fields = []
    i = 0
    if len(lyric1) < 25:
        for verse in lyric1:
            if len(verse) > 1024:
                verse = verse[0:1023]
            if verse == "":
                continue
            else:
                fields.append({"name":"\u200b","value":verse})
                i=i+1
    try:
        embed = {
            "title": song,
            "fields": fields
        }
    except:
        return '404'
    return embed

@register(group=Groups.GLOBAL, main=search, interaction=False)
async def lyrics(ctx: Context, artist: str, song: str) -> Embed:
    '''Sends Lyrics for provided song
    Params
    ------
    artist:
        Artist of the song
    song:
        Song to fetch lyrics of'''
    return await azlyrics(artist, song)

@register(group=Groups.GLOBAL, main=search, interaction=False)
async def steam(ctx: Context, game: str) -> Embed:
    '''Search Steam Index'''
    from difflib import get_close_matches
    game = " ".join(game)
    if not hasattr(ctx.bot, "index"):
        from MFramework.api.steam import loadSteamIndex
        await loadSteamIndex(ctx.bot)
    game = get_close_matches(game, ctx.bot.index.keys(), 10)
    t= ''
    for g in game:
        t += '\n- ' + g
    embed = Embed().setDescription(t[:2024])
    return embed

@register(group=Groups.GLOBAL, main=search)
async def word(ctx: Context, search: str = None) -> Embed:
    '''
    Search for a word
    Params
    ------
    search:
        Definition of word to show. Leave empty for random
    '''
    await ctx.deferred()
    url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{search}"
    r = requests.get(url)
    r = r.json()
    if type(r) is dict:
        embed = Embed()
        embed.setTitle(r.get("title", "Error"))
        embed.setDescription(r.get("message", "Not Found"))
        return embed
    embeds = []
    for entry in r[:3]:
        embed = Embed().setColor(6579043)

        embed.setTitle(entry.get("word", search).title())
        if entry.get("phonetic", None):
            embed.setFooter(f"Phonetic: {entry.get('phonetic')}")
        embed.addField("Origin", entry.get("origin", "-"), True)

        meanings = []
        for meaning in entry.get("meanings", [])[:3]:
            part = meaning.get('partOfSpeech')
            for definition in meaning.get("definitions", {}):
                result = f"- *({part})* {definition['definition']}"
                if definition.get("example", None):
                    result += "\n**Example**: " + definition['example']
                if definition.get("synonyms", None):
                    result += "\n**Synonyms**: " + ", ".join(definition["synonyms"][:5])
                    if len(definition["synonyms"]) > 5:
                        result += "..."
                if definition.get("antonyms", None):
                    result += "\n**Antonyms**: " + ", ".join(definition["antonyms"][:5])
                    if len(definition["antonyms"]) > 5:
                        result += "..."
                meanings.append(result)
        embed.setDescription("\n\n".join(meanings))

        embeds.append(embed)
    return embeds