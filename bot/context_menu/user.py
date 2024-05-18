from MFramework import Context, Groups, Guild_Member, User, register


@register(group=Groups.MODERATOR, auto_defer=False, name="Warn")
async def Warn(ctx: Context, user: User):
    """
    Warn user
    Params
    ------
    user:
        user to warn
    """
    from bot.infractions.interactions import Reason, Row, TextInput

    return Reason(
        Row(TextInput("Reason", placeholder="Reason of this action")), title="Infraction", custom_id=f"Warn-{user.id}"
    )
