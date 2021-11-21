from mlib.localization import check_translation, tr
from MFramework import Context, Embed, register, Groups
from MFramework.commands._utils import commands, command_shortcuts, commands_regex, COMPILED_REGEX, aliasList, reactions
@register(group=Groups.GLOBAL, interaction=False)
async def help(ctx: Context, command: str=None, *, language):
    '''Shows detailed help message for specified command alongside it's parameters, required permission, category and example usage.
    Params 
    ------
    command:
        Command to show detailed help info for - Example: command
    '''
    group = ctx.permission_group
    embed = Embed()
    if command:
        cmd = command
        translated_cmd = check_translation(f"commands.{cmd}.cmd_trigger", language, cmd)
        embed.setTitle(tr("commands.help.title", language, command=translated_cmd))
        embed.setDescription(check_translation(f'commands.{cmd}.cmd_extended_help', language, ""))
        _h = check_translation(f'commands.{cmd}.cmd_help', language, '')
        if _h != '':
            embed.addField(tr('commands.help.short_desc', language), _h)
        return await ctx.reply(embeds=[embed])
    desc = tr('commands.help.available_triggers', language, botid=ctx.bot.user_id, botname=ctx.bot.username, alias=ctx.bot.alias) + "\n"
    if ctx.cache.alias != ctx.bot.alias:
        desc += tr('commands.help.server_trigger', language, server_alias=ctx.cache.alias) + "\n"
    desc += "\n" + tr('commands.help.example_command', language, alias=ctx.bot.alias) + "\n"
    embed.setDescription(desc)
    allowed_commands = list(filter(lambda x: x.group >= group and x.group <= Groups.GLOBAL, commands.values()))
    string = ""
    for cmd in filter(lambda x: not x.interaction, allowed_commands):
        if cmd.guild and cmd.guild != ctx.guild_id:
            continue
        _cmd = check_translation(f'commands.{cmd.name}.cmd_trigger', language, cmd.name)
        _sig = check_translation(f'commands.{cmd.name}.cmd_signature', language, None)
        if not _sig:
            _sig = ' '.join(list(f'[{i.name}]' for i in filter(lambda x: 'positional' in x.kind.lower(), cmd.arguments.values()) if i.name not in {'ctx', 'args'}))
        _help = check_translation(f'commands.{cmd.name}.cmd_help', language, cmd.help)
        string += f"**{ctx.cache.alias or ctx.bot.alias}{_cmd}**"
        string += f" {_sig}" if _sig != '' else ""
        string += f" - {_help}" if _help != '' else ""
        string += '\n'
        try:
            alias = check_translation(f'commands.{cmd.name}.cmd_alias', language, list(aliasList.keys())[list(aliasList.values()).index(cmd.name)])
            if alias != '':
                string += tr(f'commands.help.alias_message', language, alias=alias)
        except:
            pass
    string += '\n'
    if string != '':
        embed.addFields("Message commands", string)
    string = ""
    a = [i for i in allowed_commands]
    for cmd in filter(lambda x: x.interaction, allowed_commands):
        if cmd.guild and cmd.guild != ctx.guild_id:
            continue
        if ' ' in cmd.name or cmd.name.istitle():
            continue
        string += f"**/{cmd.name}**"
        string += f" - {cmd.help.strip()}"
        string += '\n'
    if string != '':
        embed.addFields("Slash Commands", string)
    embed.setColor(ctx.cache.color).setFooter(tr('commands.help.yourPerm', language, group=group))
    await ctx.reply(embeds=[embed])
