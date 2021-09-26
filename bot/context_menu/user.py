from MFramework import register, Groups, Context, User, Guild_Member

@register(group=Groups.GLOBAL)
async def Infractions(ctx: Context, user: User):
    '''
    Shows user Infractions
    Params
    ------
    user:
        User which infractions to show
    '''
    await ctx.deferred(private=True)
    from ..commands_slash.infractions import list_
    return await list_(ctx, user)

@register(group=Groups.GLOBAL)
async def Info(ctx: Context, member: Guild_Member):
    '''
    Shows User Info
    Params
    ------
    user:
        User to show
    '''
    await ctx.deferred(private=True)
    from ..commands_slash.info import user
    return await user(ctx, member)

@register(group=Groups.GLOBAL)
async def Experience(ctx: Context, user: User):
    '''
    Shows Experience of user
    Params
    ------
    user:
        User's exp to show
    '''
    await ctx.deferred(private=True)
    from ..commands_slash.leaderboards import exp
    return await exp(ctx, user)