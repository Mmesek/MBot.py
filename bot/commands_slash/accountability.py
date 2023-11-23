import asyncio
from datetime import datetime, timedelta

from MFramework.commands.components import Button, Button_Styles, Row

from MFramework import (
    Context,
    Groups,
    Interaction,
    Interaction_Application_Command_Callback_Data,
    Interaction_Callback_Type,
    Interaction_Response,
    Message,
    register,
)


@register(group=Groups.GLOBAL)
async def goal(ctx: Context, name: str, duration: timedelta, interval: timedelta):
    """
    Create new goal to be reminded of
    Params
    ------
    name:
        Name of the goal
    duration:
        For how long you want to receive notifications (up to 24h)
    interval:
        Interval at which to notify you. Min 5m. Digits followed by either s, m or h. Example: 30m 45s
    """
    end = datetime.now() + duration
    last_notification = datetime.now()
    buttons = Row(
        Button("Snooze", f"snooze-goal-{ctx.user_id}"),
        Button("Delete", f"delete-goal-{ctx.user_id}", style=Button_Styles.DANGER),
    )
    dm = await ctx.bot.create_dm(ctx.user_id)
    if not dm:
        return "Can't notify you as I can not send you a direct message!"

    await ctx.reply(f"Got it, will notify you every {interval} for {duration}!")

    while True:
        if datetime.now() > end:
            return
        if last_notification < datetime.now() - interval:
            msg = await ctx.send_dm(
                f"Hey, have you completed your objective? Your goal was `{name}`", components=[buttons]
            )
            response = await wait_for_continue(ctx, msg)
            if "delete" in response:
                return
        await asyncio.sleep(abs((datetime.now() - (last_notification + interval)).total_seconds()))


async def wait_for_continue(ctx: Context, msg: Message):
    try:
        interaction: Interaction = await ctx.bot.wait_for(
            "interaction_create",
            check=lambda x: (
                x.data.custom_id == f"Button-snooze-goal-{ctx.user_id}"
                or x.data.custom_id == f"Button-delete-goal-{ctx.user_id}"
            )
            and (x.user or x.member.user).id == ctx.user_id,
            timeout=300,
        )
        await ctx.bot.create_interaction_response(
            interaction.id,
            interaction.token,
            Interaction_Response(
                type=Interaction_Callback_Type.UPDATE_MESSAGE,
                data=Interaction_Application_Command_Callback_Data(components=[]),
            ),
        )
        return interaction.data.custom_id
    except TimeoutError:
        await msg.edit(components=[])
        return
