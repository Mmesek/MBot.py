from MFramework import register, Groups, Context, Embed
from MFramework.commands.components import TextInput

@register(group=Groups.GLOBAL)
async def suggestion(ctx: Context, title: TextInput[1, 100], your_suggestion: TextInput[1, 4000]) -> str:
    '''
    Make a `Server Suggestion`!
    Params
    ------
    title: Short
        Title of suggestion
    your_suggestion: Long
        Your suggestion
    '''
    e = Embed()
    e.set_author(str(ctx.user), icon_url=ctx.user.get_avatar())
    e.set_title(title)
    e.set_description(your_suggestion)
    #e.set_color()#TODO
    webhook = ctx.cache.webhooks.get("suggestion", None)
    if not webhook:
        return "There is no channel configured to accept suggestions!"
    # Webhook-based:
    m = await ctx.bot.execute_webhook(webhook[0], webhook[1], wait=True, embeds=[e])
    await m.react("👍")
    await m.react("👎")
    return "Suggestion sent!"
    # Message-based:
    # Buttons on message? That would require counter but could be prettier
