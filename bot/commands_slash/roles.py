from typing import List
import enum
from MFramework import register, Groups, Context, Snowflake, ChannelID, RoleID, Role, Component_Types, Button_Styles, Select_Option, Emoji
from MFramework.commands.components import Select, Option, Row, Button

@register(group=Groups.MODERATOR)
async def role(ctx: Context, *args, language, **kwargs):
    '''Manages Roles'''
    pass

@register(group=Groups.MODERATOR, main=role)
async def button(ctx: Context, *, language):
    '''
    Description to use with help command
    '''
    pass

class Button_Types(enum.Enum):
    Primary = Button_Styles.PRIMARY.name
    Secondary = Button_Styles.SECONDARY.name
    Success = Button_Styles.SUCCESS.name
    Danger = Button_Styles.DANGER.name
    Select = Component_Types.SELECT_MENU.name

class RoleSelect(Select):
    private_response = True
    @classmethod
    async def execute(cls, ctx: Context, data: str, values: List[str], not_selected: List[Select_Option]) -> str:
        added = []
        removed = []
        for value in values:
            if value == "None":
                continue
            if int(value) not in ctx.member.roles:
                await ctx.bot.add_guild_member_role(ctx.guild_id, ctx.user_id, value, "Interaction Role - Select")
                added.append(value)
        for option in not_selected:
            if option.value == "None":
                continue
            if int(option.value) in ctx.member.roles:
                await ctx.bot.remove_guild_member_role(ctx.guild_id, ctx.user_id, option.value, "Interaction Role - Select")
                removed.append(option.value)
        msg = []
        if added:
            msg.append(f"Added: {', '.join([f'<@&{id}>' for id in added])}")
        if removed:
            msg.append(f"Removed: {', '.join([f'<@&{id}>' for id in removed])}")
        if not msg:
            msg.append("No change")
        await ctx.reply("\n".join(msg))

class RoleButton(Button):
    private_response = True
    @classmethod
    async def execute(cls, ctx: Context, data: str) -> str:
        if int(data) not in ctx.member.roles:
            await ctx.bot.add_guild_member_role(ctx.guild_id, ctx.user_id, data, "Interaction Role - Select")
            msg = f"Added <@&{data}>"
        else:
            await ctx.bot.remove_guild_member_role(ctx.guild_id, ctx.user_id, data, "Interaction Role - Button")
            msg = f"Removed <@&{data}>"
        await ctx.reply(msg)


class CurrentRoles(Button):
    private_response = True
    @classmethod
    async def execute(cls, ctx: Context, data: str) -> str:
        picked = []
        for row in ctx.data.message.components:
            for select_component in filter(lambda x: x.type == Component_Types.SELECT_MENU, row.components):
                for value in select_component.options:
                    if int(value.value) in ctx.member.roles:
                        picked.append(value)        
        msg = ", ".join([f"<@{id}>" for id in picked])
        await ctx.reply(msg or "None")


@register(group=Groups.MODERATOR, main=button, private_response=True)
async def create(ctx: Context, 
                role: Role, 
                message_id: Snowflake = None, 
                label: str = None, 
                emoji: str = None, 
                group: str = None, 
                style: Button_Types = Button_Styles.PRIMARY, 
                description: str = None, 
                disabled: bool= False, 
                default: bool = False, 
                placeholder: str = None, 
                min_picks: int = 0, 
                max_picks: int = 1,
                update: bool = False
    ):
    '''
    Adds new interaction role button/option
    Params
    ------
    role:
        Role that should be toggled on click
    message_id:
        ID of bot's Message that should have this interaction role assigned to
    label:
        Name of this button or option (Defaults to Role's name)
    emoji:
        Emoji to use as an icon for button or option
    group:
        [Select] Selection group for this role (for example for One of or Unique)
    disabled:
        Whether this button or Selection should be disabled by default
    style:
        [Button] Style of the button
    description:
        [Select] Description of this role for option
    default:
        [Select] Whether this option should be default in selection
    placeholder:
        [Select] Selection's default name when no choice is specified
    min_picks:
        [Select] Minimal amount of roles to pick in this selection (0-25)
    max_picks:
        [Select] Maximal amount of roles to pick in this selection (0-25)
    update:
        Whether to update existing values
    '''
    if not message_id:
        message_id = ctx.channel.last_message_id

    msg = await ctx.bot.get_channel_message(ctx.channel_id, message_id)

    if msg.author.id != ctx.bot.user_id:
        return "Sorry, I can add interactions only to my own messages!"

    if emoji:
        emoji = emoji.strip('<>').split(":")
        if len(emoji) == 1:
            emoji.append(None)
        emoji = Emoji(id=emoji[-1], name=emoji[-2], animated='a' == emoji[0])


    place_found = False

    if style is not Button_Types.Select:
        btn = RoleButton(label or role.name, role.id, Button_Styles.get(style.value), emoji, disabled)
        opt = None
    else:
        btn = None
        opt = Option(label or role.name, role.id, description, emoji, default)

    for row in msg.components:
        if btn and len(row.components) < 5 and row.components and row.components[0].type is not Component_Types.SELECT_MENU:
            row.components.append(btn)
            place_found = True
        elif opt and row.components and row.components[0].type is Component_Types.SELECT_MENU and all(i in row.components[0].custom_id.split("-") for i in {str(group), "RoleSelect"}):
            if len(row.components[0].options) < 25:
                row.components[0].options.append(opt)
                if update:
                    row.components[0].max_values = max_picks
                    row.components[0].min_values = min_picks
                if placeholder:
                    row.components[0].placeholder = placeholder
                place_found = True

    if not place_found and len(msg.components) == 5:
        return "This message have already exhausted limits!"

    if not place_found:
        if btn:
            msg.components.append(Row(btn))
        elif opt:
            msg.components.append(Row(RoleSelect(opt, custom_id=group, placeholder=placeholder, min_values=min_picks, max_values=max_picks, disabled=disabled)))

    await msg.edit()
    return "Role added!"

@register(group=Groups.MODERATOR, main=button)
async def edit(ctx: Context, role: Role, message_id: Snowflake, group: str = None, description: str = None, emoji: str = None, placeholder: str = None, min_picks: int=None, max_picks: int=None):
    '''
    Edits existing interaction roles
    Params
    ------
    group:
        [Select] Selection group to edit
    placeholder:
        [Select] Selection's default name when no choice is specified
    min_picks:
        [Select] Minimal amount of roles to pick in this selection (0-25)
    max_picks:
        [Select] Maximal amount of roles to pick in this selection (0-25)
    '''
    msg = await ctx.bot.get_channel_message(ctx.channel_id, message_id)
    if emoji:
        emoji = emoji.strip('<>').split(":")
        if len(emoji) == 1:
            emoji.append(None)
        emoji = Emoji(id=emoji[-1], name=emoji[-2], animated='a' == emoji[0])

    if msg.author.id != ctx.bot.user_id:
        return "Sorry, I can add interactions only to my own messages!"

    for row in msg.components:
        if row.components and row.components[0].type is Component_Types.SELECT_MENU and all(i in row.components[0].custom_id.split("-") for i in {str(group), "RoleSelect"}):
            if len(row.components[0].options) < 25:
                if max_picks:
                    row.components[0].max_values = max_picks
                if min_picks:
                    row.components[0].min_values = min_picks
                if placeholder:
                    row.components[0].placeholder = placeholder
                for option in row.components[0].options:
                    if option.value == str(role.id):
                        option.description = description
                        option.emoji = emoji
    await msg.edit()
    return "Role edited!"

@register(group=Groups.MODERATOR, main=button, private_response=True)
async def empty_option(ctx: Context, select_group: str, message_id: Snowflake = None, label: str = "None", description: str = None, emoji: str = None):
    """
    Adds "Clear all" selection option that does nothing (Allows clearing roles from selection)
    Params
    ------
    select_group:
        Group to which option should be added
    message_id:
        Message to which option should be added
    label:
        Name of option (Default: None)
    description:
        Description of option
    emoji:
        Emoji of option
    """
    if not message_id:
        message_id = ctx.channel.last_message_id
    msg = await ctx.bot.get_channel_message(ctx.channel_id, message_id)
    if emoji:
        emoji = emoji.strip('<>').split(":")
        if len(emoji) == 1:
            emoji.append(None)
        emoji = Emoji(id=emoji[-1], name=emoji[-2], animated='a' == emoji[0])
    btn_added = False
    for row in msg.components:
        if row.components and row.components[0].type is Component_Types.SELECT_MENU and all(i in row.components[0].custom_id.split("-") for i in {str(select_group), "RoleSelect"}):
            for x, option in enumerate(row.components[0].options):
                if option.value == "None":
                    row.components[0].options.pop(x)
                    break
            if len(row.components[0].options) < 25:
                row.components[0].options.append(Option(label, "None", description, emoji))
                btn_added = True
            else:
                return "This Selection doesn't have any space left! (25 options)"
    if btn_added:
        await msg.edit()
        return "Cleanup selection added!"
    return "Couldn't find suitable Selection"


@register(group=Groups.MODERATOR, main=button, private_response=True)
async def info(ctx: Context, message_id: Snowflake=None, *, language):
    '''
    Shows info about Interaction Roles associated with this message
    Params
    ------
    message_id:
        Message to query
    '''
    if not message_id:
        message_id = ctx.channel.last_message_id
    msg = await ctx.bot.get_channel_message(ctx.channel_id, message_id)
    components = []
    for row in msg.components:
        if row.components and row.components[0].type is Component_Types.SELECT_MENU:
            components.append(row.components[0].custom_id)
            for option in row.components[0].options:
                components.append(f"{option.label} - {option.value}")
    return "\n".join(components)


@register(group=Groups.MODERATOR, main=role)
async def reaction(ctx: Context, *args, language, **kwargs):
    '''Manages Reaction Roles'''
    pass

@register(group=Groups.MODERATOR, main=reaction, aliases=['rra'])
async def create(ctx: Context, emoji: str, role: RoleID, group: str = None, channel: ChannelID = None, message_id: Snowflake = None, *args, language, **kwargs):
    '''
    Adds new reaction role
    Params
    ------
    emoji:
        Emoji to use as a reaction
    role:
        Role that should be given for reacting
    group:
        Whether this RR should belong to a group
    channel:
        Channel in which RR should be created. Empty means current channel
    message_id:
        Message ID under which RR should be created. Empty means last message in channel
    '''
    from mlib.utils import replaceMultiple
    reaction = f"{emoji}:0" if ":" not in emoji else replaceMultiple(emoji, ['<:', '>'], '')
    if group not in ctx.cache.reaction_roles:
        ctx.cache.reaction_roles[group] = {message_id: {reaction: [role]}}
    else:
        if message_id not in ctx.cache.reaction_roles[group]:
            ctx.cache.reaction_roles[group][message_id] = {reaction: [role]}
        else:
            ctx.cache.reaction_roles[group][message_id][reaction] = [role]
    from MFramework.database.alchemy import models, types
    s = ctx.db.sql.session()
    r = models.Role.fetch_or_add(s, server_id = ctx.guild_id, id=role)
    r.add_setting(types.Setting.ChannelID, channel)
    r.add_setting(types.Setting.MessageID, message_id)
    r.add_setting(types.Setting.Reaction, reaction)
    if group:
        r.add_setting(types.Setting.Group, group)
    s.commit()
    await ctx.bot.create_reaction(channel, message_id, replaceMultiple(emoji, ['<:', '>'], ''))
    await ctx.reply(f"Successfully created reaction {emoji} for role <@&{role}>", private=True)

#@register(group=Groups.MODERATOR, main=reaction, aliases=['rre'])
async def edit(ctx: Context, emoji: str, role: RoleID, group: str = None, channel: ChannelID = None, message_id: Snowflake = None, *args, language, **kwargs):
    '''
    Edits existing reaction role
    Params
    ------
    emoji:
        Emoji to use as a reaction
    role:
        Role that should be given for reacting
    group:
        Whether this RR should belong to a group
    channel:
        Channel in which RR should be edited. Empty means current channel
    message_id:
        Message ID under which RR should be edited. Empty means last message in channel
    '''
    # FIXME!
    await ctx.bot.delete_own_reaction(channel, message_id, emoji)
    await ctx.bot.create_reaction(channel, message_id, emoji)
    return await ctx.reply("Successfully modified reaction role")

@register(group=Groups.MODERATOR, main=reaction, aliases=['rrd'])
async def remove(ctx: Context, emoji: str = None, role: RoleID = None, group: str = None, channel: ChannelID = None, message_id: Snowflake = None, *args, language, **kwargs):
    '''
    Removes existing reaction role
    Params
    ------
    emoji:
        Emoji to remove from being reaction emoji
    role:
        Role to remove from being reaction role
    group:
        Whether this RR should be removed from belonging to a group
    channel:
        Channel from which RR should be removed. Empty means current channel
    message_id:
        Message ID under which RR should be removed. Empty means last message in channel
    '''
    from MFramework.database.alchemy import models, types
    s = ctx.db.sql.session()
    if role:
        r = models.Role.filter(s, server_id = ctx.guild_id, id=role).first()
    elif emoji:
        from mlib.utils import replaceMultiple
        r = models.Role.with_setting(types.Setting.Reaction, replaceMultiple(emoji, ['<:', '>'], '')).filter(server_id=ctx.guild_id).first()
    else:
        return ctx.reply("Either Emoji or Role has to be specified", private=True)
    if group:
        r.remove_setting(types.Setting.Group)
        s.commit()
        return
    emoji = r.remove_setting(types.Setting.Reaction)
    channel = r.remove_setting(types.Setting.ChannelID)
    message_id = r.remove_setting(types.Setting.MessageID)
    group = r.remove_setting(types.Setting.Group)
    s.commit()
    ctx.cache.reaction_roles.get(group, {}).get(message_id, {}).pop(emoji, None)
    if ctx.cache.reaction_roles.get(group, {}).get(message_id, None) == {}:
        ctx.cache.reaction_roles.get(group, {}).pop(message_id, None)
        if ctx.cache.reaction_roles.get(group, None) == {}:
            ctx.cache.reaction_roles.pop(group)
    await ctx.bot.delete_own_reaction(channel, message_id, emoji)
    await ctx.reply(f"Successfully deleted <@&{role}> from being a {emoji if ':0' in emoji else '<:'+emoji+'>'} reaction role", private=True)

class RoleTypes:
    AND = "AND"
    OR = "OR"
    COMBINED = "COMBINED"

#@register(group=Groups.ADMIN, main=role)
async def level(ctx: Context, role: RoleID, req_exp: int= 0, req_voice: int= 0, type: RoleTypes = RoleTypes.AND, stacked: bool=False, *, language):
    '''Management of level roles

    Params
    ------
    role:
        Role which should be awarded for reaching these values
    req_exp:
        Chat exp required to gain this role
    req_voice:
        Voice exp required to gain this role
    type:
        Whether both, either or in total exp should award this role
    '''
    pass