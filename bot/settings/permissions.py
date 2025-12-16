import difflib

from MFramework import Application_Command_Permission_Type, Embed, Groups, RoleID, UserID, register
from MFramework.commands._utils import commands, detect_group

from bot import Context, database as db
from bot.database import models
from bot.settings import settings


@register(group=Groups.MODERATOR, main=settings, private_response=True)
async def permission(ctx: Context):
    """
    Permissions related commands
    """


@register(group=Groups.MODERATOR, main=permission, private_response=True)
async def get(ctx: Context, command: str) -> Embed:
    """
    Fetches set permissions for this command
    Params
    ------
    command:
        command to get permissions of
    """
    current = ctx.permission_group

    cmd = commands.get(command, None)
    if not cmd:
        return await ctx.reply("{}".format(difflib.get_close_matches(command, commands)))
    command_group = cmd.group
    registered = list(filter(lambda i: i.name == command, ctx.bot.registered_commands))
    if registered:
        registered = registered[0]
    cmd_id = registered.id
    slash_cmd = await ctx.bot.get_application_command_permissions(ctx.bot.application.id, ctx.guild_id, cmd_id)
    roles = []
    e = Embed()
    e.add_field("Current Group", current)
    e.add_field("Command Group", command_group)

    for role in filter(lambda x: x.type == Application_Command_Permission_Type.ROLE, slash_cmd.permissions):
        if role.permission:
            roles.append(role.id)
    if roles:
        roles = "\n".join([f"- <@&{i}>" for i in roles])
        e.addField("Set Role permissions", roles)
    users = []
    for user in filter(lambda x: x.type == Application_Command_Permission_Type.USER, slash_cmd.permissions):
        if user.permission:
            users.append(user.id)
    if users:
        users = "\n".join([f"- <@{i}>" for i in users])
        e.addField("Set User permissions", users)
    return e


@register(group=Groups.MODERATOR, main=permission, private_response=True)
async def user(ctx: Context, user: UserID) -> Embed:
    """
    Fetches permission level of selected user
    Params
    ------
    user:
        User to fetch permission level of
    """
    user = await ctx.cache.members[int(user)]
    roles = user.roles
    user = user.user.id
    group = detect_group(ctx.bot, user, ctx.guild_id, roles)
    e = Embed().add_field("Provided user", f"<@{user}>").add_field("Detected group", group)
    return e


@register(group=Groups.MODERATOR, main=permission, private_response=True)
async def command(group: str) -> Embed:
    """
    Fetches commands available in selected permission level
    Params
    ------
    group:
        Group to list commands of
    """
    group = Groups.get(group.upper())

    _commands = filter(lambda x: x.group == group, commands.values())
    e = Embed().set_description("\n".join([f"- {i.name}" for i in _commands]))
    return e


@register(group=Groups.OWNER, main=permission, private_response=True)
async def group(ctx: Context, role: RoleID, permission_level: Groups | None = None, *, session: db.Session):
    """
    Configure Role permission for bot management
    Params
    ------
    role:
        Role to configure
    permission:
        Permission level this role should have
    """
    if not ctx.permission_group.can_use(permission_level or Groups.GLOBAL):
        return f"You can't set role to permission higher than your own ({ctx.permission_group.name.title()})"

    _role: models.Role = await models.Role.fetch_or_add(
        session, models.Role.server_id == ctx.guild_id, models.Role.id == role
    )
    if not permission_level:
        if _role:
            group = Groups.get(_role.permissions)
        else:
            group = Groups.GLOBAL
        return f"Current Permission level for <@&{role}> is `{group.name.title()}`"
    _role.permissions = permission_level.value
    ctx.cache.groups[permission_level].add(role)
    return f"Permission Level for <@&{role}> is now `{permission_level.name.title()}`"
