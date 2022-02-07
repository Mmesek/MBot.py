from MFramework import Groups, Context
from MFramework.commands.decorators import reaction

@reaction("📌", group=Groups.SUPPORTER)
async def pin(ctx: Context, *args):
    '''
    Pin's message
    '''
    if next(filter(lambda x: x.emoji.name == '📌', ctx.data.reactions)).count >= 3:
        try:
            await ctx.bot.add_pinned_channel_message(ctx.channel_id, ctx.message_id, "User pinned message")
        except:
            msgs = await ctx.bot.get_pinned_messages(ctx.channel_id)
            await ctx.bot.unpin_message(ctx.channel_id, msgs[0].id, "Too many pins to pin a new message")
            await ctx.bot.add_pinned_channel_message(ctx.channel_id, ctx.message_id, "Users voted to pin a message")

@reaction("poll", group=Groups.GLOBAL)
async def poll(ctx: Context, *args):
    await ctx.data.react("✅")
    await ctx.data.react("❎")

@reaction("🗑️")
async def delete(ctx: Context, *args):
    invoking_user = ctx.user_id
    invoking_permission = ctx.permission_group
    msg = await ctx.data.get()
    ctx.user_id = msg.author.id
    member = ctx.cache.members.get(ctx.user_id)
    if member:
        ctx.member = member
    if not invoking_permission.can_use(ctx.permission_group):
        return
    reaction = next(filter(lambda x: x.emoji.name == '🗑️', msg.reactions))
    if reaction.count >= 5:
        await ctx.data.delete(reason="Users voted to remove message")
