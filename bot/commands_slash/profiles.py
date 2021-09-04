from MFramework import register, Groups, Context, Embed
from MFramework.database.alchemy import models

from mlib.localization import secondsToText, tr

#@register(group=Groups.GLOBAL)
async def profile():
    '''Management of settings related to bot's user profile'''
    pass

from datetime import datetime
@register(group=Groups.GLOBAL, main=profile, default=True)
async def show(ctx: Context, *, language):
    '''Shows User Profile'''
    e = Embed().setAuthor(ctx.user.username, None, ctx.user.get_avatar())
    s = ctx.db.sql.session()
    u = models.User.fetch_or_add(s, id=ctx.user_id)
    if u.Language is not None:
        e.addField(tr('commands.profile.language', language), u.Language, True)
    if u.Birthday is not None:
        e.addField(tr('commands.profile.birthday', language), u.Birthday.strftime("%A, %B\n%d/%m/%Y"), True)
    if len(e.fields) == 2:
        e.addField("\u200b", "\u200b", True)
    total_exp = 0
    total_vexp = 0
    exp = u.statistics
    for server_exp in exp:
        total_exp += server_exp.EXP
        total_vexp += server_exp.vEXP
    if total_exp != 0:
        e.addField(tr('commands.profile.totalEXP', language), str(total_exp), True)
    if total_vexp != 0:
        e.addField(tr('commands.profile.totalVoiceTime', language), secondsToText(total_vexp, language.upper()), True)
    if u.Color is not None:
        e.setColor(u.Color)
    regional = []
    if u.Timezone is not None:
        regional.append(tr('commands.profile.timezone', language, timezone=u.Timezone))
    if u.Region is not None:
        regional.append(tr('commands.profile.region', language, region=u.Region))
    if u.Currency is not None:
        regional.append(tr('commands.profile.currency', language, currency=u.Currency))
    if regional != []:
        e.addField(tr('commands.profile.regional', language), '\n'.join(regional))
                
    dates = tr('commands.profile.datesDiscord', language, discord=(ctx.user.id).strftime('%Y-%m-%d %H:%M:%S')) + '\n'
    dates += tr('commands.profile.datesServer', language, server=datetime.fromisoformat(ctx.member.joined_at).strftime('%Y-%m-%d %H:%M:%S'))
    #"Discord: {discord}\nServer: {server}".format(discord=created(ctx.user.id).strftime('%Y-%m-%d %H:%M:%S'), server=datetime.fromisoformat(ctx.member.joined_at).strftime('%Y-%m-%d %H:%M:%S'))
    if ctx.member.premium_since:
        dates += tr('commands.profile.datesBoostStart', language, boost=datetime.fromisoformat(ctx.member.premium_since).strftime('%Y-%m-%d %H:%M:%S'))
        #'\nBooster: {boost}'.format(boost=datetime.fromisoformat(ctx.member.premium_since).strftime('%Y-%m-%d %H:%M:%S'))
    e.addField(tr('commands.profile.datesJoined', language), dates, True)
    await ctx.embed(ctx.channel_id, "", e.embed)

@register(main=profile)
async def birthday(ctx: Context, year: int=1, month: int=1, day: int=1, *, language):
    '''Set your birthday'''
    s = ctx.db.sql.session()
    c = models.User.fetch_or_add(s, id=ctx.user_id)
    from datetime import date
    c.Birthday = date(int(year), int(month), int(day))
    s.merge(c)
    s.commit()

@register(main=profile)
async def language(ctx: Context, new_language, *, language):
    '''Set your language'''
    s = ctx.db.sql.session()
    c = models.User.fetch_or_add(s, id=ctx.user_id)
    import pycountry
    try:
        new_language = pycountry.languages.lookup(new_language).alpha_2
    except LookupError:
        return await ctx.message(ctx.channel, tr('commands.profile.notFoundLanguage', language, language=new_language))#f"Couldn't find language {new_language}")
    c.Language = new_language
    s.merge(c)
    s.commit()
    #ctx.cache.Users[ctx.user.id].language = new_language

@register(main=profile)
async def color(ctx: Context, hex_color, *, language):
    '''Set your prefered colour'''
    s = ctx.db.sql.session()
    c = models.User.fetch_or_add(s, id=ctx.user_id)
    c.Color = int(hex_color.strip('#'), 16)
    s.merge(c)
    s.commit()
    
@register(main=profile)
async def timezone(ctx: Context, timezone, *, language):
    '''Set your timezone'''
    s = ctx.db.sql.session()
    c = models.User.fetch_or_add(s, id=ctx.user_id)
    import pytz
    timezone = timezone.lower().replace('utc', 'Etc/GMT').replace('gmt', 'Etc/GMT')
    if any(timezone.lower() == i.lower() for i in pytz.all_timezones):
        c.Timezone = timezone.replace('+','MINUS').replace('-','PLUS').replace('MINUS','-').replace('PLUS','+')
    else:
        return await ctx.message(ctx.channel_id, tr('commands.profile.notFoundTimezone', language, timezone=timezone))#f"Couldn't find Timezone {timezone}.")
    s.merge(c)
    s.commit()

@register(main=profile)
async def region(ctx: Context, region, *, language):
    '''Set your region'''
    s = ctx.db.sql.session()
    c = models.User.fetch_or_add(s, id=ctx.user_id)
    import pycountry
    try:
        region = pycountry.countries.search_fuzzy(region)[0].alpha_2
    except LookupError:
        return await ctx.message(ctx.channel, tr('commands.profile.notFoundRegion', language, region=region))#f"Couldn't find region {region}")
    c.Region = region
    s.merge(c)
    s.commit()

@register(main=profile)
async def currency(ctx: Context, currency, *, language):
    '''Set your prefered currency'''
    s = ctx.db.sql.session()
    c = models.User.fetch_or_add(s, id=ctx.user_id)
    import pycountry
    try:
        region = pycountry.currencies.lookup(currency).alpha_3
    except LookupError:
        return await ctx.message(ctx.channel, tr('commands.profile.notFoundCurrency', language, currency=currency))
    c.Currency = currency
    s.merge(c)
    s.commit()

@register(main=profile)
async def gender(ctx: Context, gender, *, language):
    '''Set your prefered pronounce'''
    s = ctx.db.sql.session()
    c = models.User.fetch_or_add(s, id=ctx.user_id)
    if gender[0] not in ['M','F','W']:
        return await ctx.message(ctx.channel, tr('commands.profile.notFoundGender', language))
    c.Gender = gender
    s.merge(c)
    s.commit()