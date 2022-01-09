from MFramework import Context, User, Groups, register
from .Halloween import general, fear # noqa: F401
from .Christmas import general, snowballs # noqa: F401

@register(group=Groups.GLOBAL)
async def event(ctx: Context, *, language):
    '''Event related commands'''
    pass

@register(group=Groups.GLOBAL, main=event, default=True)
async def help(ctx: Context, *, language):
    '''Shows help related to Event'''
    # Possibly move to help?
    pass

@register(group=Groups.GLOBAL, main=event)
async def leaderboard(ctx: Context, *, language):
    '''Shows event Leaderboards'''
    # TODO: MOVE TO LEADERBOARDS!
    pass

@register(group=Groups.GLOBAL, main=event)
async def history(ctx: Context, user: User=None, *, language):
    '''Shows User's event history

    Params
    ------
    user:
        User's history to show
    '''
    pass

@register(group=Groups.GLOBAL, main=event)
async def stats(ctx: Context, *, language):
    '''Shows faction statistics'''
    pass

@register(group=Groups.GLOBAL, main=event)
async def profile(ctx: Context, user: User=None, *, language):
    '''Shows User's event profile

    Params
    ------
    user:
        User's profile to show
    '''
    pass

@register(group=Groups.GLOBAL, main=event)
async def cooldown(ctx: Context, *, language):
    '''Shows Current cooldowns'''
    pass

@register(group=Groups.MODERATOR, main=event)
async def summary(ctx: Context, *, language):
    '''Shows summary of Current Event'''
    pass
