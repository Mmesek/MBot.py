from MFramework import Groups, register


@register(group=Groups.MODERATOR)
async def role():
    """Manages Roles"""
    pass


from . import buttons, levels, reactions  # noqa: F401
