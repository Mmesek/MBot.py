from MFramework import register, Groups, Context, Embed, UserID


@register(group=Groups.MODERATOR, interaction=False)
async def permission(ctx: Context):
    '''
    Permissions related commands
    '''
    pass

@register(group=Groups.MODERATOR, interaction=False, main=permission)
async def get(ctx: Context, command: str) -> Embed:
    '''
    etches set permissions for this command
    Params
    ------
    command:
        command to get permissions of
    '''
    current = ctx.permission_group
    from MFramework.commands._utils import commands
    cmd = commands.get(command, None)
    if not cmd:
        import difflib
        return await ctx.reply("{}".format(difflib.get_close_matches(command, commands)))
    command_group = cmd.group
    registered = list(filter(lambda i: i.name == command, ctx.bot.registered_commands))
    if registered:
        registered = registered[0]
    cmd_id = registered.id
    slash_cmd = await ctx.bot.get_application_command_permissions(ctx.bot.application.id, ctx.guild_id, cmd_id)
    roles = []
    e = Embed()
    e.addField("Current Group", current)
    e.addField("Command Group", command_group)
    from MFramework import Application_Command_Permission_Type
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

@register(group=Groups.MODERATOR, interaction=False, main=permission)
async def user(ctx: Context, user: UserID) -> Embed:
    '''
    Description to use with help command
    Params
    ------
    user:
        description
    '''
    from MFramework.commands._utils import detect_group
    user = ctx.cache.members[int(user)]
    roles = user.roles
    user = user.user.id
    group = detect_group(ctx.bot, user, ctx.guild_id, roles)
    e = Embed().addField("Provided user", f"<@{user}>").addField("Detected group", group)
    return e

@register(group=Groups.MODERATOR, interaction=False, main=permission)
async def command(ctx: Context, group: str) -> Embed:
    '''
    Description to use with help command
    Params
    ------
    group:
        description
    '''
    group = Groups.get(group.upper())
    from MFramework.commands._utils import commands
    _commands = filter(lambda x: x.group == group, commands.values())
    e = Embed().setDescription("\n".join([f"- {i.name}" for i in _commands]))
    return e
