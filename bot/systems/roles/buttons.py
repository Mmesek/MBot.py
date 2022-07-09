import enum

from MFramework import (
    Button_Styles,
    Component_Types,
    Context,
    Emoji,
    Groups,
    Role,
    Select_Option,
    Snowflake,
    register,
)
from MFramework.commands.components import Button, Option, Row, Select

from . import role


@register(group=Groups.MODERATOR, main=role)
async def button():
    """
    Management of Interaction-based roles
    """
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
    async def execute(cls, ctx: Context, data: str, values: list[str], not_selected: list[Select_Option]) -> str:
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
                await ctx.bot.remove_guild_member_role(
                    ctx.guild_id, ctx.user_id, option.value, "Interaction Role - Select"
                )
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
async def create(
    ctx: Context,
    role: Role,
    message_id: Snowflake = None,
    label: str = None,
    emoji: str = None,
    group: str = None,
    style: Button_Types = Button_Styles.PRIMARY,
    description: str = None,
    disabled: bool = False,
    default: bool = False,
    placeholder: str = None,
    min_picks: int = 0,
    max_picks: int = 1,
    update: bool = False,
):
    """
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
    """
    if not message_id:
        message_id = ctx.channel.last_message_id

    msg = await ctx.bot.get_channel_message(ctx.channel_id, message_id)

    if msg.author.id != ctx.bot.user_id:
        return "Sorry, I can add interactions only to my own messages!"

    if emoji:
        emoji = emoji.strip("<>").split(":")
        if len(emoji) == 1:
            emoji.append(None)
        emoji = Emoji(id=emoji[-1], name=emoji[-2], animated="a" == emoji[0])

    place_found = False

    if style is not Button_Types.Select:
        btn = RoleButton(label or role.name, role.id, Button_Styles.get(style.value), emoji, disabled)
        opt = None
    else:
        btn = None
        opt = Option(label or role.name, role.id, description, emoji, default)

    for row in msg.components:
        if (
            btn
            and len(row.components) < 5
            and row.components
            and row.components[0].type is not Component_Types.SELECT_MENU
        ):
            row.components.append(btn)
            place_found = True
        elif (
            opt
            and row.components
            and row.components[0].type is Component_Types.SELECT_MENU
            and all(i in row.components[0].custom_id.split("-") for i in {str(group), "RoleSelect"})
        ):
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
            msg.components.append(
                Row(
                    RoleSelect(
                        opt,
                        custom_id=group,
                        placeholder=placeholder,
                        min_values=min_picks,
                        max_values=max_picks,
                        disabled=disabled,
                    )
                )
            )

    await msg.edit()
    return "Role added!"


@register(group=Groups.MODERATOR, main=button)
async def edit(
    ctx: Context,
    role: Role,
    message_id: Snowflake,
    group: str = None,
    description: str = None,
    emoji: str = None,
    placeholder: str = None,
    min_picks: int = None,
    max_picks: int = None,
):
    """
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
    """
    msg = await ctx.bot.get_channel_message(ctx.channel_id, message_id)
    if emoji:
        emoji = emoji.strip("<>").split(":")
        if len(emoji) == 1:
            emoji.append(None)
        emoji = Emoji(id=emoji[-1], name=emoji[-2], animated="a" == emoji[0])

    if msg.author.id != ctx.bot.user_id:
        return "Sorry, I can add interactions only to my own messages!"

    for row in msg.components:
        if (
            row.components
            and row.components[0].type is Component_Types.SELECT_MENU
            and all(i in row.components[0].custom_id.split("-") for i in {str(group), "RoleSelect"})
        ):
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
async def empty_option(
    ctx: Context,
    select_group: str,
    message_id: Snowflake = None,
    label: str = "None",
    description: str = None,
    emoji: str = None,
):
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
        emoji = emoji.strip("<>").split(":")
        if len(emoji) == 1:
            emoji.append(None)
        emoji = Emoji(id=emoji[-1], name=emoji[-2], animated="a" == emoji[0])

    btn_added = False
    for row in msg.components:
        if (
            row.components
            and row.components[0].type is Component_Types.SELECT_MENU
            and all(i in row.components[0].custom_id.split("-") for i in {str(select_group), "RoleSelect"})
        ):
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
async def info(ctx: Context, message_id: Snowflake = None):
    """
    Shows info about Interaction Roles associated with this message
    Params
    ------
    message_id:
        Message to query
    """
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
