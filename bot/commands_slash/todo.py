from MFramework import Context, Embed, Groups, register
from MFramework.commands.components import Button, Button_Styles, Modal, Row, TextInput


class ToggleTodo(Button):
    private_response: bool = True

    @classmethod
    async def execute(cls, ctx: Context, data: str):
        owner_id, state = data.split("-")
        if int(owner_id) != ctx.user_id:
            return "You are not todo's owner!"

        if state == "undone":
            ctx.data.message.content = f"~~{ctx.data.message.content}~~"
            ctx.data.message.components = [
                Row(
                    ToggleTodo(
                        label=f"Done by {ctx.user.username}",
                        custom_id=f"{ctx.user_id}-done",
                        style=Button_Styles.SUCCESS,
                    ),
                    EditTodo(label="Edit", custom_id=ctx.user_id, style=Button_Styles.SECONDARY),
                )
            ]
            state = "off"
        else:
            ctx.data.message.content = ctx.data.message.content[2:-2]
            ctx.data.message.components = [
                Row(
                    ToggleTodo(
                        label=f"To Do: {ctx.user.username}",
                        custom_id=f"{ctx.user_id}-undone",
                        style=Button_Styles.DANGER,
                    ),
                    EditTodo(label="Edit", custom_id=ctx.user_id, style=Button_Styles.SECONDARY),
                )
            ]
            state = "on"

        ctx.data.message._Client = ctx.bot
        await ctx.data.message.edit()
        return f"Toggled {state}"


class EditTodo(Button):
    auto_deferred: bool = False

    @classmethod
    async def execute(cls, ctx: Context, data: str):
        if int(data) != ctx.user_id:
            return "Only todo's owner can modify this todo!"
        return Todo(
            Row(
                TextInput(
                    "Note's description",
                    custom_id="description",
                    max_length=1900,
                    value=ctx.data.message.content,
                    placeholder="Something to do...",
                )
            ),
            title="Edit Todo",
            custom_id=ctx.data.message.id,
        )


class Todo(Modal):
    @classmethod
    async def execute(cls, ctx: "Context", data: str, inputs: dict[str, str]):
        if data:
            if not inputs["description"]:
                await ctx.bot.delete_message(ctx.channel_id, data, "Todo's removed via Edit")
                return "Note removed"
            msg = await ctx.bot.get_channel_message(ctx.channel_id, data)
            await msg.edit(inputs["description"])
        return f"Edited successfully"


@register(group=Groups.MODERATOR)
async def todo(ctx: Context, description: TextInput[1, 1900] = "Note's description") -> Embed:
    """
    Make a new todo task!
    Params
    ------
    description:
        description of task
    """
    await ctx.reply(
        content=description,
        components=[
            Row(
                ToggleTodo(
                    label=f"To Do: {ctx.user.username}", custom_id=f"{ctx.user_id}-undone", style=Button_Styles.DANGER
                ),
                EditTodo(label="Edit", custom_id=ctx.user_id, style=Button_Styles.SECONDARY),
            ),
        ],
    )
