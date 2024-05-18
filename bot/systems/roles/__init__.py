from MFramework import Groups, register


@register(group=Groups.MODERATOR)
async def role():
    """Manages Roles"""
    pass


from bot.systems.roles import buttons, levels, reactions  # noqa: F401
