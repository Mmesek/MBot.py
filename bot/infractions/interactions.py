from MFramework import Context, Groups, Guild_Member, Snowflake, User
from MFramework.commands.components import (
    Button,
    Button_Styles,
    Emoji,
    Modal,
    Row,
    Select,
    Select_Option,
    TextInput,
)


class ExpireInfractions(Select):
    @classmethod
    async def execute(cls, ctx: "Context", data: str, values: list[str], not_selected: list[Select_Option]):
        if ctx.permission_group.can_use(Groups.ADMIN):
            from .commands import expire

            ctx = Context(ctx.bot.cache, ctx.bot, ctx.data, expire._cmd)

            return await expire(ctx, values[0])
        return "Only Admins can expire infractions!"


class Reason(Modal):
    private_response = False

    @classmethod
    async def execute(cls, ctx: Context, data: str, inputs: dict[str, str]):
        action, id = data.split("-")
        member: Guild_Member = ctx.cache.members.get(int(id))
        if member:
            user = member.user
        else:
            user = User(id=data)
        from .commands import ban, kick, timeout, warn

        ctx = Context(ctx.bot.cache, ctx.bot, ctx.data, warn._cmd)

        if action == "Warn":
            return await warn(ctx, user, inputs.get("Reason", "Instant Action"))
        elif action == "Mute":
            return await timeout(ctx, user, inputs.get("Reason", "Instant Action"))
        elif action == "Kick":
            return await kick(ctx, user, inputs.get("Reason", "Instant Action"))
        elif action == "Ban":
            return await ban(ctx, user, inputs.get("Reason", "Instant Action"))


class InstantAction(Button):
    auto_deferred: bool = False

    def __init__(
        self, label: str, custom_id: str = None, style: Button_Styles = ..., emoji: Emoji = None, disabled: bool = False
    ):
        super().__init__(label, custom_id or label, style, emoji, disabled)

    @classmethod
    async def execute(cls, ctx: Context, data: str):
        if not ctx.permission_group.can_use(Groups.MODERATOR):
            return "You can't use this button!"
        return Reason(Row(TextInput("Reason", placeholder="Reason of this action")), title="Infraction", custom_id=data)


def instant_actions(id: Snowflake):
    _instant_actions = Row(
        InstantAction("Warn", style=Button_Styles.PRIMARY, emoji=Emoji(name="📖")),
        InstantAction("Mute", style=Button_Styles.SECONDARY, emoji=Emoji(name="🔕")),
        InstantAction("Kick", style=Button_Styles.SECONDARY, emoji=Emoji(name="🏌️‍♂️")),
        InstantAction("Ban", style=Button_Styles.DANGER, emoji=Emoji(name="🔨")),
    )
    for ia in _instant_actions.components:
        ia.custom_id += f"-{id}"
    return _instant_actions
