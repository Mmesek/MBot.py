from MFramework import Context, Groups, Guild_Member, User, register


@register(group=Groups.GLOBAL, private_response=True)
async def Infractions(ctx: Context, user: User):
    """
    Shows user Infractions
    Params
    ------
    user:
        User which infractions to show
    """
    await ctx.deferred(private=True)
    from ..commands_slash.infractions import list_

    return await list_(ctx, user)


@register(group=Groups.GLOBAL, private_response=True)
async def Info(ctx: Context, member: Guild_Member):
    """
    Shows User Info
    Params
    ------
    user:
        User to show
    """
    await ctx.deferred(private=True)
    from ..commands_slash.info import user

    return await user(ctx, member)


@register(group=Groups.GLOBAL, private_response=True)
async def Experience(ctx: Context, user: User):
    """
    Shows Experience of user
    Params
    ------
    user:
        User's exp to show
    """
    await ctx.deferred(private=True)
    from ..commands_slash.leaderboards import exp

    return await exp(ctx, user)


@register(group=Groups.MODERATOR, auto_defer=False, name="Warn")
async def Warn(ctx: Context, user: User):
    """
    Warn user
    Params
    ------
    user:
        user to warn
    """
    from ..commands_slash.infractions import Reason, Row, TextInput

    return Reason(
        Row(TextInput("Reason", placeholder="Reason of this action")), title="Infraction", custom_id=f"Warn-{user.id}"
    )
