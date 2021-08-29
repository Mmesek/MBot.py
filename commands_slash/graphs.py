from MFramework import register, Groups, Context
from mlib.localization import tr

@register(group=Groups.ADMIN, interaction=False)
async def graph(ctx: Context, graph='all', resample='Y', locator='Month', interval=4, *args, growth=False, language, **kwargs):
    '''Possible arguments: graph=all/joined/created/boosters\nresample=W-MON/M/Y/dunnowhatelse\nmonth_interval=1+ probably\n-growth'''
    import time, asyncio
    b = time.time()
    import pandas as pd
    import matplotlib.pyplot as plt
    from mlib import graphing
    from MFramework.utils.utils import created, truncate
    from datetime import date

    f = time.time()
    await ctx.deferred()

    #Gather data here
    server = ctx.cache
    m_retries = 0
    if len(server.joined) != server.member_count:
        if len(server.joined) >= server.member_count:
            server.joined = []
        await ctx.bot.request_guild_members(ctx.guild_id)
    while len(server.joined) != server.member_count and len(server.joined) < server.member_count:
        await asyncio.sleep(0.1)
        m_retries+=1
        if m_retries == 75:
            break
    s = time.time()

    #Create figure and plot data here
    s_member = ctx.cache.joined
    total = {'joined':[], 'created':[], 'premium':[]}
    for each in s_member:
        t = pd.to_datetime(each[1]).tz_convert(None) #Joined
        c = pd.to_datetime(created(each[0])).tz_localize(None)  #Created
        try:
            p = pd.to_datetime(each[2]).tz_convert(None)  #Premium
            total['premium'] += [p]
        except:
            pass
        total['joined'] += [t]
        total['created'] += [c]
    sd = time.time()
    total['joined'] = sorted(total['joined'])
    total['created'] = sorted(total['created'])
    total['premium'] = sorted(total['premium'])
    d = time.time()

    fig, ax = plt.subplots()

    if graph == 'all' or graph == 'joined':
        if growth:
            df = pd.Series(total['joined'], index=total['joined'])

            df = df.resample(resample).count()
            idf = pd.to_datetime(df.index)
            ax.plot(idf, df, label=tr('commands.graph.joined', language), linestyle='-')
        else:
            df = pd.Series(total['joined'])
            ax.plot(df, df.index, label=tr('commands.graph.joined', language))
    
    if graph == 'all' or graph=='created':
        cr = pd.Series(total['created'], index=total['created'])
    
        cr = cr.resample(resample).count()
        icr = pd.to_datetime(cr.index)
        ax.plot(icr, cr, label=tr('commands.graph.created', language), marker='o')
    if graph == 'all' or graph == 'boosters':
        if growth:
            pr = pd.Series(total['premium'], index=total['premium'])
            pr = pr.resample(resample).count()
            ipr = pd.to_datetime(pr.index)
            ax.plot(ipr, pr, label=tr('commands.graph.boosters', language), marker='.')
        else:
            pr = pd.Series(total['premium'])
            ax.plot(pr, pr.index, label=tr('commands.graph.boosters', language), marker='.')


    graphing.set_locator(ax, locator, interval)

    fig.autofmt_xdate()


    #Set Names
    graphing.set_legend(ax, tr('commands.graph.growth', language), tr('commands.graph.memberCount', language), tr('commands.graph.dates', language))

    fig.tight_layout()
    img_str = graphing.create_image(fig)
    stats = tr('commands.graph.stats', language, total=truncate(time.time()-d, 2), gather=truncate(s-f,2), sort=truncate(d-sd,2), convert=truncate(sd-s,2), imp=truncate(f-b,2))
    await ctx.reply(content=stats, file=img_str, filename=f"growth-{date.today()}.png")#f"Took ~{truncate(time.time()-d,2)}s\n{truncate(s-f,2)}s to gather\n{truncate(d-sd,2)}s to sort\n{truncate(sd-s,2)}s to convert\n{truncate(f-b,2)}s to import stuff")

@register(group=Groups.ADMIN, interaction=False)
async def graph_infractions(ctx: Context, infraction_type='all', resample='D', locator='Week', interval=1, *args, moderator=None, user=None, growth=False, language, **kwargs):
    '''Plot infractions over days'''
    import time
    b = time.time()
    from mlib import graphing
    import pandas as pd
    import matplotlib.pyplot as plt
    from MFramework.utils.utils import truncate
    from datetime import date
    f = time.time()
    await ctx.deferred()
    _s = ctx.db.sql.session()
    import MFramework.database.alchemy.log as db
    infractions = _s.query(db.Infractions).filter(db.Infraction.server_id == ctx.guild_id)
    if infraction_type != 'all':
        infractions = infractions.filter(db.Infraction.type == infraction_type)
    if moderator != None:
        infractions = infractions.filter(db.Infraction.moderator_id == moderator)
    if user != None:
        infractions = infractions.filter(db.Infraction.user_id == user)
    infractions = infractions.all()
    s = time.time()
    total = {'Total Infractions': []}
    table = {
        "warn": "Warnings",
        "tempmute": "Temp Mutes",
        "mute": "Mutes",
        "unmute": "Unmutes",
        "kick": "Kicks",
        "tempban":"Temp Bans",
        "ban": "Bans",
        "unban": "Unbans"
    }
    for i in table.values():
        total[i] = []
    total['Others'] = []
    for each in infractions:
        i = pd.to_datetime(each.Timestamp).tz_convert(None)
        total[table.get(each.InfractionType, 'Others')] += [i]
        total['Total Infractions'] += [i]

    sd = time.time()
    
    for i in total:
        total[i] = sorted(total[i])
    
    d = time.time()
    fig, ax = plt.subplots()

    for i in total:
        if total[i] == []:
            continue
        if not growth:
            df = pd.Series(total[i], index=total[i])
    
            df = df.resample(resample).count()
            idf = pd.to_datetime(df.index)
            ax.plot(idf, df, label=i)#tr('commands.graph.infractions', language), marker='o')
        else:
            df = pd.Series(total[i])
            ax.plot(df, df.index, label=i)#tr('commands.graph.infractions', language))

    graphing.set_locator(ax, locator, interval)
    fig.autofmt_xdate()

    #Set Names
    graphing.set_legend(ax, tr('commands.graph.infractions', language), tr('commands.graph.infractionCount', language), 'Dates (D/M)')
    fig.tight_layout()
    
    img_str = graphing.create_image(fig)
    stats = tr('commands.graph.stats', language, total=truncate(time.time()-d, 2), gather=truncate(s-f,2), sort=truncate(d-sd,2), convert=truncate(sd-s,2), imp=truncate(f-b,2))
    await ctx.reply(stats, file=img_str, filename=f"growth-{date.today()}.png")

@register(group=Groups.ADMIN, interaction=False)
async def graph_words(ctx: Context, channel_id, *word_or_phrase, limit_messages=10000, resample='W-MON', locator='Week', interval=1, growth=False, language, **kwargs):
    '''Plots word usage over days'''
    import time
    b = time.time()
    from mlib import graphing
    import matplotlib.pyplot as plt
    import pandas as pd
    from MFramework.utils.utils import truncate
    from datetime import date
    f = time.time()
    await ctx.deferred()


    word_or_phrase = ''.join(word_or_phrase)
    limit_messages = int(limit_messages)
    if limit_messages < 100:
        limit = limit_messages
    else:
        limit = 100
    total_messages = await ctx.bot.get_channel_messages(channel_id, limit=limit)
    previous_id = 0
    previous_first_id = 0
    cache = ctx.cache.messages
    channel_id = int(channel_id)
    if channel_id in cache:
        cached_messages = list(i[1] for i in sorted(cache[channel_id].items()))
        #print("Last Message:", total_messages[0].content)
        #print("First Cached Messaged:", cached_messages[0].content)
        #print("Last Cached Messaged:", cached_messages[-1].content)
        if total_messages[0].id > cached_messages[-1].id:
            print("old cache?")
            last_id = cached_messages[-1]
            old = True
        else:
            print("Cache up to date")
            old = False
            total_messages = cached_messages
    if limit_messages > 100:
        for i in range(int((int(limit_messages)) / 100)):
            last_id = total_messages[-1].id
            first_id = total_messages[0].id
            print(previous_id, last_id, previous_id > last_id, len(total_messages))
            if previous_id > last_id or previous_id == 0: #and previous_first_id < first_id:
                new_messages = await ctx.bot.get_channel_messages(channel_id, after=last_id)
                #if new_messages[0] != total_messages[0] and new_messages[-1] != total_messages[-1]:
                total_messages += new_messages
                previous_id = last_id
                previous_first_id = first_id
            else:
                break
    for msg in reversed(total_messages):
        if msg.id not in ctx.cache.messages[channel_id]:
            ctx.cache.message(msg.id, msg)
    total_messages = list(i[1] for i in sorted(ctx.cache.messages[channel_id].items()))

    s = time.time()

    total = {word_or_phrase: []}
    sorted_total = {word_or_phrase: []}
    for message in total_messages:
        if word_or_phrase in message.content:
            message_timestamp = pd.to_datetime(message.timestamp).tz_convert(None)
            total[word_or_phrase] += [message_timestamp]
    sd = time.time()

    if total[word_or_phrase] == []:
        return await ctx.reply(f"Couldn't find specified word or phrase ({word_or_phrase}) within last fetchable {len(total_messages)} in <#{channel_id}>")
    #for i in total:
    #    sorted_total[i] = sorted(total[i])

    d = time.time()
    fig, ax = plt.subplots()

    for i in total:
        if total[i] == []:
            continue
        if not growth:
            df = pd.Series(total[i], index=total[i])
    
            df = df.resample(resample).count()
            idf = pd.to_datetime(df.index)
            ax.plot(idf, df, label=i, marker='o')#tr('commands.graph.infractions', language), marker='o')
        else:
            df = pd.Series(total[i])
            ax.plot(df, df.index, label=i)#tr('commands.graph.infractions', language))

    graphing.set_locator(ax, locator, interval)
    fig.autofmt_xdate()

    #Set Names
    graphing.set_legend(ax, tr('commands.graph.words', language), tr('commands.graph.wordCount', language), 'Dates (D/M)')
    fig.tight_layout()

    img_str = graphing.create_image(fig)
    stats = tr('commands.graph.stats', language, total=truncate(time.time()-d, 2), gather=truncate(s-f,2), sort=truncate(d-sd,2), convert=truncate(sd-s,2), imp=truncate(f-b,2))
    await ctx.reply(f"Found {len(total[word_or_phrase])} messages containing `{word_or_phrase}` within {len(total_messages)} of total fetched messages. (Took {truncate(s-f,2)}s to fetch them)", file=img_str, filename=f"growth-{date.today()}.png")

