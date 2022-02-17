from MFramework import register, Groups, Interaction, Embed, Context

@register()
async def convert(ctx: Context, interaction: Interaction, *args, language, **kwargs):
    '''Converts things'''
    pass

@register(group=Groups.GLOBAL, main=convert, private_response=True)
async def morse(ctx: Context, message: str, decode: bool=False, *args, language, **kwargs):
    '''Decodes or Encodes message in Morse
    
    Params
    ------
    message:
        Message to encode or decode
    decode:
        Whether to decode from or encode to Morse'''
    morse_dict = {
        'A':'.-', 'B':'-...', 'C':'-.-.', 'D':'-..', 'E':'.', 
        'F':'..-.', 'G':'--.', 'H':'....', 'I':'..', 'J':'.---', 
        'K':'-.-', 'L':'.-..', 'M':'--', 'N':'-.', 'O':'---', 
        'P':'.--.', 'Q':'--.-', 'R':'.-.', 'S':'...', 'T':'-', 
        'U':'..-', 'V':'...-', 'W':'.--', 'X':'-..-', 'Y':'-.--', 
        'Z':'--..', '1':'.----', '2':'..---', '3':'...--', '4':'....-', 
        '5':'.....', '6':'-....', '7':'--...', '8':'---..', '9':'----.', 
        '0':'-----', ', ':'--..--', '.':'.-.-.-', '?':'..--..', '/':'-..-.', 
        '-':'-....-', '(':'-.--.', ')':'-.--.-', '`':'.----.', '!':'-.-.--',
        '&':'.-...',':':'---...',';':'-.-.-.','=':'-...-','+':'.-.-.',
        '_':'..--.-','"':'.-..-.','$':'...-..-','@':'.--.-.',
        'Ĝ':'--.-.','Ĵ':'.---.','Ś':'...-...','Þ':'.--..','Ź':'--..-.','Ż':'--..-','Ð':'..-..',
        'Error':'........','End of Work':'...-.-','Starting Signal':'-.-.-',
        'Understood':'...-.'
    }
    morse_sequences = {
        ". .-. .-. --- .-.":"........",
        ". -. -.. -....- --- ..-. -....- .-- --- .-. -.-":"...-.-",
        "..- -. -.. . .-. ... - --- --- -..":"...-."
    }
    inverted = {v: k for k, v in morse_dict.items()}
    def encrypt(message):
        cipher=''
        for letter in message.upper():
            if letter == ' ':
                cipher+='/'
                #cipher+=morse_dict['-']+' '
                continue
            elif letter not in morse_dict:
                cipher+=letter+' '
            else:
                cipher+=morse_dict.get(letter,'') + ' '
        for sequence in morse_sequences:
            if sequence in cipher:
                cipher = cipher.replace(sequence, morse_sequences[sequence])
        return cipher
    def decrypt(message):
        message += ' '
        decipher = ''
        morse = ''
        for letter in message:
            if letter == '/':
                decipher +=' '
            elif letter not in '.-' and letter != ' ':
                decipher += letter
            elif letter != ' ':
                morse += letter
            elif letter == ' ' and morse != '':
                decipher += inverted.get(morse,'\nNo match for: "'+morse+'"\n')
                morse = ''
        return decipher
    org = message
    if decode:
        reward = decrypt(message)
        t = "Morse -> Normal"
    else:
        reward = encrypt(message)
        t = "Normal -> Morse"
    if len(org) > 2000:
        org = org[:100] + f"\n(+{len(org)-100} more characters)\nCharacter limit exceeded."
    if len(reward) > 2048:
        t=t+f" | Not sent {len(reward)-2048} characters due to limit of 2048"
        reward = reward[:2048]
    await ctx.reply('Orginal: '+org, [Embed(title=t, description=reward)])

@register(group=Groups.GLOBAL, main=convert, interaction=False, private_response=True)
async def roman(ctx: Context, value: str) -> str:
    '''Converts Roman to digits, or vice versa
    value:
        Value to convert'''
    #Very simple and does not really work (Well, it works but if you mess up digit it does not really check that)
    #Sources:
    # https://www.w3resource.com/python-exercises/class-exercises/python-class-exercise-1.php 
    # https://www.w3resource.com/python-exercises/class-exercises/python-class-exercise-2.php
    # https://www.oreilly.com/library/view/python-cookbook/0596001673/ch03s24.html
    def int_to_Roman(num):
        val = [
            1000, 900, 500, 400,
            100, 90, 50, 40,
            10, 9, 5, 4,
            1
            ]
        syb = [
            "M", "CM", "D", "CD",
            "C", "XC", "L", "XL",
            "X", "IX", "V", "IV",
            "I"
            ]
        roman_num = ''
        i = 0
        while  num > 0:
            for _ in range(num // val[i]):
                roman_num += syb[i]
                num -= val[i]
            i += 1
        return roman_num
    def roman_to_int(s):
        rom_val = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
        int_val = 0
        for i in range(len(s)):
            if i > 0 and rom_val[s[i]] > rom_val[s[i - 1]]:
                int_val += rom_val[s[i]] - 2 * rom_val[s[i - 1]]
            else:
                int_val += rom_val[s[i]]
        return int_val
    value = ''.join(value)
    if value.isdigit():
        value = int(value)
        r = int_to_Roman(value)
        s = f'Int: {value} -> Roman: {r}'
    else:
        try:
            r = roman_to_int(value)
            s = f'Roman: {value} -> Int: {r}'
        except KeyError:
            s = f'An error occured, perhas non roman numeral was provided? Only `I`, `V`, `X`, `L`, `C`, `D` and `M` are allowed'
    return str(s)

@register(group=Groups.GLOBAL, main=convert)
async def timeunits(ctx: Context, duration: int, from_unit: str='s', to: str='w', *, language) -> str:
    '''Converts for example 3600s into 1h. Works with s, m, h, d and w
    duration:
        Value to calculate
    from_unit:
        Base unit from which to convert. S for second, M for Minute, H for Hour, D for Day and W for Week
    to:
        Opposite to from_unit. Accepts same values'''
    from mlib.converters import total_seconds
    from mlib.localization import secondsToText
    return secondsToText(total_seconds(f"{duration}{from_unit}").total_seconds(), language)

@register(group=Groups.GLOBAL, main=convert)
async def timezone(ctx: Context, yymmdd: str='YYYY-MM-DD', hhmm:str='HH:MM', timezones: str=[], *args, language) -> Embed:
    '''Shows current time in specified timezone(s)
    yymmdd:
        Base Date
    hhmm:
        Base Hour
    timezones:
        Targeted timezones'''
    import pytz
    import datetime
    from mlib.localization import tr
    _timezones = []
    now = datetime.datetime.now()
    if ':' in yymmdd or (yymmdd.isdigit() and not hhmm.isdigit()):
        if 'HH:MM' != hhmm:
            timezones = [hhmm, *timezones]
        hhmm = yymmdd
        yymmdd = 'YYYY-MM-DD'
        year = now.year
        month = now.month
        day = now.day
    elif 'YYYY-MM-DD' != yymmdd and ('-' in yymmdd or yymmdd.isdigit()):
        yymmdd = yymmdd.split('-')
        if len(yymmdd) == 3:
            year = int(yymmdd[0])
            month = int(yymmdd[1])
            day = int(yymmdd[2])
        elif len(yymmdd) == 2:
            year = now.year
            month = int(yymmdd[0])
            day = int(yymmdd[1])
        else:
            year = now.year
            month = now.month
            day = int(yymmdd[0])
    elif yymmdd.lower() in ['tomorrow', 'yesterday']:
        now += datetime.timedelta(days=1 if yymmdd == 'tomorrow' else -1)
        year = now.year
        month = now.month
        day = now.day
    else:
        if yymmdd != 'YYYY-MM-DD':
            _timezones.append(yymmdd)
            yymmdd = 'YYYY-MM-DD'
        year = now.year
        month = now.month
        day = now.day
    if hhmm != 'HH:MM' and (':' in hhmm or hhmm.isdigit()):
        is_digit = hhmm.isdigit()
        has_colon = ':' in hhmm
        hhmm = hhmm.split(':')
        if len(hhmm) == 2:
            hour = int(hhmm[0])
            minute = int(hhmm[1])
        else:
            hour = int(hhmm[0])
            minute = 0
    else:
        if hhmm != 'HH:MM':
            _timezones.append(hhmm)
            hhmm = 'HH:MM'
        hour = now.hour
        minute = now.minute
    timezones = [timezones]#(*_timezones, *timezones)
    _timezones = []
    if 'in' in timezones or 'to' in timezones:
        if any(i == timezones[0] for i in ['in', 'to']):
            #use default
            from_timezone = 'UTC'
            timezones = timezones[1:]
        elif any(i == timezones[1] for i in ['in', 'to']):
            from_timezone = timezones[0]
            timezones = timezones[2:]
    else:
        #use default
        from_timezone = 'UTC'
    if yymmdd != 'YYYY-MM-DD' or hhmm != 'HH:MM' or from_timezone != 'UTC':
        if (('gmt+' in from_timezone.lower()) or ('gmt-' in from_timezone.lower())) and 'etc/' not in from_timezone.lower():
            from_timezone = from_timezone.lower().replace('gmt', 'Etc/GMT')
        try:
            _dt = pytz.timezone(from_timezone).localize(datetime.datetime(year, month, day, hour, minute, 0))
        except:
            return await ctx.reply(tr('commands.timezone.timezoneNotFound', language, from_timezone=from_timezone))#f"Couldn't find timezone {from_timezone}")
        #_dt = tz#datetime.datetime(year=year, month=month, day=day, hour=hour, minute=minute, second=0, microsecond=0, tzinfo=tz)
        utc_dt = _dt.astimezone(pytz.timezone('UTC'))
        base = _dt.isoformat()
    else:
        base = ctx.data.timestamp
        utc_dt = datetime.datetime.fromisoformat(base)
        #tz = pytz.timezone('UTC').localize(datetime.datetime(utc_dt.year, utc_dt.month, utc_dt.day, utc_dt.hour, utc_dt.minute, utc_dt.second))
        _dt = utc_dt
    e = Embed().setFooter(f"UTC {utc_dt.strftime('%Y-%m-%d %H:%M:%S')}").setTimestamp(base)
    if from_timezone != 'UTC':
        e.setDescription(f"{from_timezone}: {_dt.strftime('%Y-%m-%d %H:%M:%S %Z%z')}")
    for timezone in timezones:
        if 'gmt' in timezone.lower() and 'etc/' not in timezone.lower():
            timezone = timezone.lower().replace('gmt', 'Etc/GMT').replace('+','MINUS').replace('-','PLUS').replace('MINUS','-').replace('PLUS','+')
        try:
            #tz = pytz.timezone(timezone)
            #tz = tz.localize(datetime.datetime(_dt.year, _dt.month, _dt.day, _dt.hour, _dt.minute, 0))
            dt = _dt.astimezone(pytz.timezone(timezone))
            dt = dt.strftime('%Y-%m-%d %H:%M:%S %Z%z')
        except pytz.UnknownTimeZoneError:
            dt = tr('commands.timezone.notFound', language)
        except Exception as ex:
            dt = ex
        if len(e.fields) <= 25:
            e.addField(timezone, dt)
    return e

@register(group=Groups.GLOBAL, main=convert, private_response=True)
async def upside(ctx: Context, text: str) -> str:
    '''Makes text uʍop ǝpᴉsdn!
    text:
        Text to invert'''
    import upsidedown
    return upsidedown.transform(text)

@register(group=Groups.GLOBAL, main=convert, private_response=True)
async def rot(ctx: Context, message: str, shift: int=13, alphabet: str='ABCDEFGHIJKLMNOPQRSTUVWXYZ') -> Embed:
    '''Caesar Cipher
    message:
        Message to rotate
    shift:
        Value to rotate by
    alphabet:
        Alphabet to use'''
    dict_alphabet = {}
    msg = '`'
    for x, letter in enumerate(alphabet):
        dict_alphabet[letter] = x
#        msg += f'{x+1+int(shift)}. {letter} '
#        if x % 5 == 0 and x != 0:
#            msg += '\n'
    shifted = ''
    for x, letter in enumerate(alphabet):
        y = int(x) + int(shift)
        if y > 25:
            y = y-26
        shifted += alphabet[y]
    msg += shifted
    msg += '`'
    from_key = ''
    new_key = []
    try_key = message
    for k in try_key:
        if not k.isdigit() and k.upper() in alphabet:
            new_key.append(dict_alphabet[k.upper()])
        else:
            new_key.append(' ')
    if new_key != []:
        key = new_key
    for k in key:
        try:
            _key = int(k) + int(shift)
            if _key > 25:
                _key = _key - 26
            from_key += alphabet[_key]
        except:
            from_key += k
    e = Embed().addField("Alphabet", f"`{alphabet}`\n"+msg).setDescription(from_key)
    return e

@register(group=Groups.GLOBAL, main=convert, private_response=True)
async def hex2dec(ctx: Context, value: str) -> int:
    '''
    Convert hexadecimal value to Decimal
    Params
    ------
    value:
        Hex value to convert
    '''
    return int(value, base=16)

@register(group=Groups.GLOBAL, main=convert, private_response=True)
async def dec2hex(ctx: Context, value: int) -> int:
    '''
    Convert decimal value to Hexadecimal
    Params
    ------
    value:
        Decimal value to convert
    '''
    return hex(value)

@register(group=Groups.GLOBAL, main=convert, interaction=False, private_response=True)
async def asciitohex(ctx: Context, ascii_:str) -> Embed:
    '''Converts Ascii to Numbers
    ascii_:
        Value to Convert'''
    f = Embed().setTitle('Ascii to Hex').setDescription(ascii_)
    f.addField('Dec',str(int.from_bytes(bytearray(ascii_, 'ascii'),'big'))[2:1023])
    f.addField('Bin',str(bin(int.from_bytes(bytearray(ascii_, encoding='ascii'), 'big')))[2:1023])
    f.addField('Hex',str(hex(int.from_bytes(bytearray(ascii_, encoding='ascii'), 'big')))[2:1023])
    f.addField('Oct',str(oct(int.from_bytes(bytearray(ascii_, encoding='ascii'), 'big')))[2:1023])
    return f

@register(group=Groups.GLOBAL, main=convert)
async def currency(ctx: Context, amount: float=1, from_currency: str="EUR", to_currency: str="USD", *, language) -> str:
    '''Converts currency
    amount:
        Amount to convert
    from_currency:
        Base Currency
    to_currency:
        Target Currency'''
    def check(c):
        currencies = {'€': 'EUR', '$': 'USD', '£': 'GBP'}
        return currencies.get(c, c).upper()
    #if amount.isdigit() or '.' in amount or ',' in amount:
    #    amount = float(amount.replace(',', '.').replace(' ', ''))
    from_currency, to_currency = check(from_currency), check(to_currency)
    import requests
    r = requests.get(f'https://api.exchangeratesapi.io/latest?base={from_currency}&symbols={to_currency}')
    src = ''
    try:
        result = r.json()['rates'][to_currency]
        result = "%3.2f" % (amount * float(result))
        src = "exchangeratesapi.io"
    except KeyError:
        r = requests.get(f"https://api.cryptonator.com/api/ticker/{from_currency}-{to_currency}", headers={"user-agent": "Mozilla"})
        result = r.json()#.get('error','Error')
        try:
            result = result.get('ticker', {}).get('price', 0)
            result = "%3.2f" % (amount * float(result))
            src = "cryptonator.com"
        except KeyError:
            if from_currency.lower() in ['btc', 'ltc', 'eth']:
                #"https://api.crypto.com/v1/ticker/price" this might be useful for various other crypto -> usd or crypto -> crypto
                r = requests.get(f'https://api.crypto.com/v1/ticker?symbol={from_currency.lower()}usdt')
                try:
                    result = r.json()['data']['last']
                    result = "%3.2f" % (amount * float(result))
                except KeyError:
                    result = r.json().get('msg', 'Error')
                to_currency = 'USD'
                src = "crypto.com"
            else:
                result = "Error"
    from mlib.localization import tr
    r = tr('commands.currency_exchange.result', language, result=result, to_currency=to_currency, amount=amount, currency=from_currency)
    return r+'\n'+src

@register(group=Groups.GLOBAL, main=convert, private_response=True)
async def reverse(ctx: Context, message: str, in_place: bool=False) -> str:
    '''Reverses letters
    message:
        Message to reverse
    in_place:
        Whether words should stay in place, for example -> False: elpamxe rof | True: rof elpamxe'''
    if in_place:
        r = ' '.join([i[::-1] for i in message.split(' ')])
    else:
        r = message[::-1]
    return r

@register(group=Groups.GLOBAL, main=convert)
async def electricity(ctx: Context, price: float=0.78, watts: float=1, active_hours: float=24, active_days: int=30) -> str:
    '''
    Calculate averange cost of upkeeping provided amount of watts 24/7
    Params
    ------
    price:
        Price of kWh (1000 Watts * Active hours)
    watts:
        Watts
    active_hours:
        Hours per day (Default: 24)
    active_days:
        Days in month (Default: 30)
    '''
    return f"~{round(((watts * (active_hours * active_days)) / 1000) * price, 2)} / month"

@register(group=Groups.GLOBAL, main=convert)
async def palette(ctx: Context, colors: str):
    '''
    Shows how specified colors looks like on Discord backgrounds
    Params
    ------
    colors:
        Hexadecimal colors to display. Separate multiple with comma (,) or hash (#)
    '''
    _colors = colors.replace(" ", "").split(",")
    if len(_colors) == 1:
        _colors = colors.replace(" ", "").split("#")
    colors = []
    for color in _colors:
        if not color:
            continue
        if not color.startswith("#"):
            color = "#" +str(color)
        color = color.strip()
        colors.append(color)
    from mlib.colors import buffered_image
    from PIL import Image, ImageDraw, ImageFont
    dark = "#36393F"
    mention_dark = "#49443C"
    light = "#FFFFFF"
    mention_light = "#FEEED1"
    height = len(colors) * 50
    dst = Image.new("RGBA", (1000, height))
    dst.paste(Image.new("RGBA", (150, height), dark), (400, 0))
    dst.paste(Image.new("RGBA", (150, height), mention_dark), (550, 0))
    dst.paste(Image.new("RGBA", (150, height), light), (700, 0))
    dst.paste(Image.new("RGBA", (150, height), mention_light), (850, 0))
    font = ImageFont.truetype("data/Roboto-Regular.ttf", size=15)
    color_font = ImageFont.truetype("data/Roboto-Regular.ttf", size=20)

    draw = ImageDraw.Draw(dst)
    for x, color in enumerate(colors):
        dst.paste(Image.new("RGBA", (200, 35), color), (0, x*50))
        dst.paste(Image.new("RGBA", (100, 15), color), (225, x*50 + 10))
        draw.text((60, x*50 + 5), color, font=color_font)
        draw.text((420, x*50 + 5), str(ctx.user), font=font, fill=color) # Dark
        draw.text((570, x*50 + 5), str(ctx.user), font=font, fill=color) # MentionDark
        draw.text((720, x*50 + 5), str(ctx.user), font=font, fill=color) # Light
        draw.text((870, x*50 + 5), str(ctx.user), font=font, fill=color) # MentionLight
    f = buffered_image(dst)
    await ctx.reply(file=f, filename="colors.png")
