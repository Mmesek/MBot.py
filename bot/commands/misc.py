import json
import random
import requests

from mlib.localization import tr

from MFramework import register, Context, Groups, Embed

@register(group=Groups.GLOBAL, interaction=False)
async def randomquote(ctx: Context) -> str:
    '''Sends random quote'''
    from os import path
    if not path.isfile("data/quotes.json"):
        raw = requests.get("https://raw.githubusercontent.com/dwyl/quotes/master/quotes.json")
        with open("data/quotes.json", "wb") as file:
            file.write(raw.content)
    with open("data/quotes.json", "r", newline="", encoding="utf-8") as file:
        q = json.load(file)
    r = random.SystemRandom().randrange(len(q))
    return '_'+q[r]["text"] + "_\n    ~" + q[r]["author"]


def load_words():
    with open("data/words.txt", encoding="utf-8") as word_file:
        valid_words = set(word_file.read().split())
    return valid_words


#@register(group=Groups.GLOBAL, interaction=False, notImpl=True)
async def anagram(ctx: Context, *args, **kwargs):
    '''Assembles english words from provided letters/solves anagrams'''
    words = load_words()

    await ctx.reply(words[0])


@register(group=Groups.SYSTEM, interaction=False)
async def today(ctx: Context, difference: str = None, *, language) -> Embed:
    '''Summary of what is today'''
    import datetime
    from bs4 import BeautifulSoup
    #s = sun.sun(lat=51.15, long=22.34)
    today = datetime.datetime.now()
    d = ""
    if difference != ():
        d = ''.join(difference)
        d = '-'+d if '+' not in d else d
        today = today + datetime.timedelta(days=int(d))
    month = today.month
    day = today.day
    if month <= 9:
        month = "0" + str(month)
    if day <= 9:
        day = "0" + str(day)
    t = datetime.datetime.fromisoformat(f"{today.year}-{month}-{day}T23:59")
    query = f"https://www.daysoftheyear.com/days/{today.year}/{month}/{day}/"
    r = requests.get(
        query,
        headers={"user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:65.0) Gecko/20100101 Firefox/65.0"},
    )
    if r.status_code == 200:
        soup = BeautifulSoup(r.content, "html.parser")
    else:
        return await ctx.reply(ctx.channel_id, "Error")
    f = ""
    for p in soup.find_all("h3", class_="card__title heading"):
        if "Week" in p.text or "Month" in p.text:
            continue
        else:
            f += "\n- " + p.text
    embed = Embed().setDescription(f)  # .setTitle(f"{today.year}/{month}/{day}")
    embed = embed.setTitle(today.strftime(f"%A, %B %Y (%m/%d)"))
    embed = embed.setTimestamp(datetime.datetime.now(tz=datetime.timezone.utc).isoformat())
    random.seed(today.isoformat()[:10])  # hash(today.year / today.month + today.day))
    with open("data/quotes.json", "r", newline="", encoding="utf-8") as file:
        q = json.load(file)
    quote = random.choice(q)
    #embed.addField(tr("commands.today.sun", language), tr("commands.today.sunStates", language, rise=s.sunrise(t), noon=s.solarnoon(t), set=s.sunset(t)), True)
    # embed.addField('Moon', f"Rise:\nIllumination:\nSet:", True)
    # embed.addField("Lunar Phase", f"", True)
    color = random.randint(0, 16777215)
    embed.addField(tr("commands.today.color", language), str(hex(color)).replace("0x", "#"), True).setColor(color)
    embed.addField('\u200b', '\u200b', True)
    #alternative today sources:
    #https://www.kalbi.pl/kalendarz-swiat-nietypowych
    #https://www.kalendarzswiat.pl/dzisiaj
    game_releases_url = "https://www.gry-online.pl/daty-premier-gier.asp?PLA=1"
    if '+' in d:
        game_releases_url += "&CZA=2"
    r = requests.get(game_releases_url)
    if r.status_code == 200:
        soup = BeautifulSoup(r.content, "html.parser").find('div',class_='daty-premier-2017')
    else:
        return await ctx.reply("Error")
    games = ''
    for release in soup.find_all('a', class_='box'):
        lines = release.find_all('div')
        release_date = lines[0].text
        if str(today.day) not in release_date:
            break
        p = release.find('p', class_='box-sm')
        previous_release = None
        if p:
            previous_release = p.text.replace('PC','')
        game = lines[1].contents[0]
        platform = lines[-1].text.replace(', Pudełko','')
        games += f'\n- {game} ({platform})'
        if previous_release is not None:
            games += ' | Poprzednio wydane:\n*' + previous_release.replace('\n\n', ' - ').replace('\n', '') + '*'
    if games != '':
        embed.addField("Game releases", games[:1024], True)

    r = requests.get("https://www.ign.com/upcoming/movies",
    headers={"user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:65.0) Gecko/20100101 Firefox/65.0"})
    if r.status_code == 200:
        soup = BeautifulSoup(r.content, "html.parser").find('div',class_='jsx-3629687597 four-grid')
    else:
        return await ctx.reply("Error")
    movies = ''
    if soup is not None:
        for movie in soup.find_all('a', class_='card-link'):
            lines = movie.find('div', class_='jsx-2539949385 details')#.find_all('div')
            release = lines.find('div', class_='jsx-2539949385 release-date').text
            if today.strftime("%b %d, %Y").replace(' 0', ' ') not in release:
                continue
            name = lines.find('div', class_='jsx-2539949385 name').text
            platform = lines.find('div', class_='jsx-2539949385 platform').text
            movies += f'\n- {name}' #({platform})'
    if movies != '':
        embed.addField("Movie releases", movies[:1024], True)
    # embed.addField("TV Show Episodes", f"", True)
    # embed.addField("New on Spotify", f"", True)
    # embed.addField("Song for today", f"", True)
    embed.addField(tr("commands.today.quote", language), quote["text"] + "\n- " + quote["author"])
    return embed

async def getLink(url):
    r = requests.get(
        url,
        headers={"user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:65.0) Gecko/20100101 Firefox/65.0"},
    )
    if r.status_code == 200:
        from bs4 import BeautifulSoup
        return BeautifulSoup(r.content, "html.parser")
    print(r.reason)

async def getChords(self):
    print('getting chords')
    self.chords = {}
    guitar_chords = "https://chordify.net/chord-diagrams/guitar"
    r = await getLink(guitar_chords)
    for i in r.find_all("a", class_="diagram-wrap"):
        for img in i.find_all('img'):
            self.chords[img['alt']] = 'https:' + img['src']

@register(group=Groups.GLOBAL, interaction=False)
async def chord(ctx: Context, instrument='guitar', chord: str=None) -> Embed:
    '''Sends Diagram of provided Chord for instrument'''
    if not hasattr(ctx.bot, 'chords'):
        await getChords(ctx.bot)
    t = ':('
    l = ''
    chord = ' '.join(chord)
    for chord_ in ctx.bot.chords.keys():
        if chord in chord_:
            t = chord_
            l = ctx.bot.chords[chord_]
    embed = Embed().setTitle(t).setImage(l)
    return embed


@register(group=Groups.GLOBAL, interaction=False)
async def xkcdpassword(ctx: Context) -> str:
    '''Generates random xkcd 936 styled password'''
    import secrets
    # On standard Linux systems, use a convenient dictionary file.
    # Other platforms may need to provide their own word-list.
    with open('/usr/share/dict/words') as f:
        words = [word.strip() for word in f]
        password = ' '.join(secrets.choice(words) for i in range(4))
    return password


@register(group=Groups.GLOBAL, interaction=False)
async def chord(ctx: Context, chords: str, *, all=False) -> Embed:
    '''Shows guitar chord(s) diagram(s)'''
    import json
    with open('data/chords.json','r',newline='',encoding='utf-8') as file:
        _chords = json.load(file)
    #_chords = {"Em": "022000", "C": "x32010", "A":"x02220", "G": "320033", "E": "022100", "D": "xx0232", "F": "x3321x", "Am": "x02210", "Dm": "xx0231"}
    chords = chords.split(" ")
    base_notes = "EADGBE"
    e = Embed()
    if all:
        _all = []
        for _chord in chords:
            for x in range(7):
                if x == 0:
                    if _chord in chords:
                        _all.append(f"{_chord}")
                        for i in range(5):
                            if _chord + f'_a{i+1}' in _chords:
                                _all.append(f"{_chord}_a{i+1}")    
                if _chord + f'_{x+1}' in _chords:
                    _all.append(f"{_chord}_{x+1}")
                    for i in range(5):
                        if _chord + f'_{x+1}_a{i+1}' in _chords:
                            _all.append(f"{_chord}_{x+1}_a{i+1}")
        chords = _all
    for _chord in chords:
        text = "```\n"
        try:
            _c = _chords[_chord]
        except:
            return await ctx.reply(f"Chord {_chord} not found")
        if len(_c) > 6:
            c = _c[-6:]
        for x, string in enumerate(c):
            text += string if string == 'x' else base_notes[x]
        text+='\n'
        for fret in range(1,6):
            for string in c:
                if string == str(fret):
                    text += 'O'
                else:
                    text += '|'
            text += '\n'
        text+= '```'
        if len(_c) == 7 and _c[0] not in ['0', '1']:
            #text += "\nStarting fret: " + _c[0:-6]
            _chord += f' (Fret: {_c[0:-6]})'
        e.addField(_chord, text, True)
    return e

@register(group=Groups.SYSTEM, interaction=False)
async def add_chord(ctx: Context, chord, *frets, language):
    '''Adds new chord'''
    with open('data/chords.json','r',newline='',encoding='utf-8') as file:
        _chords = json.load(file)
    _chords[chord] = ''.join(frets)
    with open('data/chords.json','w',newline='',encoding='utf-8') as file:
        json.dump(_chords, file)

@register(group=Groups.GLOBAL, interaction=False)
async def tuning(ctx: Context, tuning: str = None) -> str:
    '''Shows chords on frets for specified tuning'''
    base = ["A", "A#", "B", "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#"]
    if not tuning:
        tuning = ["E", "B", "G", "D", "A", "E"]
    else:
        tuning = [i.upper() for i in (tuning.split() if " " in tuning else tuning)]
    final = ""
    for note in tuning:
        n = base.index(note)
        final += '\n' + ' | '.join([i + ' ' if len(i) == 1 else i for i in base[n:] + base[:n+1]])
    fret_numbers = ""
    fret_numbers += ' | '.join([str(i)+' ' if len(str(i)) == 1 else str(i) for i in range(len(base)+1)])
    separator = '-' * len(fret_numbers)
    return f"```md\n{fret_numbers}\n{separator}{final}```"

'''
|_E_|_A_|_C_|_G_|_B_|_E_|
| _ | _ | _ | _ | _ | _ |
| _ | O | O | _ | _ | _ |
| _ | _ | _ | _ | _ | _ |
| _ | _ | _ | _ | _ | _ |
'''
