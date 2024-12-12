from MFramework import Channel, Channel_Types, Groups, Interaction, Webhook, register
from MFramework.utils.log import Log
from mlib.types import aInvalid
from mlib.utils import all_subclasses
from sqlalchemy import select

from bot import Context
from bot import database as db
from bot.settings import settings

# TODO:
# - Only show related subscriptions to a selected channel when unsubscribing


async def ChannelWebhooks(interaction: Interaction, current: str):
    channel_id = interaction.channel_id
    if channel_option := next(filter(lambda x: x.name == "channel" and x.value, interaction.data.options), None):
        channel_id = channel_option.value

    if not (channel := await interaction._Client.cache[interaction.guild_id].channels[channel_id]):
        channel = await interaction._Client.get_channel(channel_id)

    if channel.type in {Channel_Types.PUBLIC_THREAD, Channel_Types.PRIVATE_THREAD}:
        channel_id = channel.parent_id

    _webhooks = await interaction._Client.get_channel_webhooks(channel_id)
    mapped = {
        f"{webhook.name} by {webhook.user.global_name or webhook.user.username}": str(webhook.id)
        for webhook in _webhooks
        if current in webhook.name
    }

    if not mapped:
        return {"There are no webhooks on this channel": ""}

    if len(mapped) > 25:
        return {k: v for k, v in list(mapped.items())[:25]}
    return mapped


async def ChannelSubscriptions(ctx: Interaction, current: str, session: db.Session):
    webhook_id = None
    if webhook := next(filter(lambda x: x.name == "webhook" and x.value, ctx.data.options), None):
        webhook_id = int(webhook.value)

    _webhooks = await db.Webhook.filter(
        session,
        db.Webhook.id == webhook_id if webhook_id else db.Webhook.server_id == ctx.guild_id,
        db.Webhook.subscriptions.any(db.Subscription.source.contains(current)),
    )
    subs = [sub.source for webhook in _webhooks for sub in await webhook.awaitable_attrs.subscriptions][:25]
    return subs if subs else {"There are no subscriptions on this webhook": ""}


async def AvailableLoggers(ctx: Interaction, current: str):
    dd = ctx._Client.cache[ctx.guild_id].logging
    subs = [k for k, v in dd.items() if v is not aInvalid]
    loggers = [
        i.__name__
        for i in all_subclasses(Log)
        if current.lower() in i.__name__.lower()
        if i.__name__.lower() not in subs
    ][:25]
    return loggers if loggers else {"There are no available loggers to subscribe to": ""}


@register(Groups.ADMIN, main=settings, private_response=True)
async def logging():
    pass


@register(Groups.ADMIN, main=logging, private_response=True)
async def subscribe(
    ctx: Context, channel: Channel, webhook: ChannelWebhooks, logger: AvailableLoggers, *, session: db.Session
):
    """
    Subscribe to events via a webhook
    Params
    ------
    channel: guild_text, public_thread, private_thread
        Channel to log events to
    webhook:
        Webhook to use for logging. Leave empty to use existing bot-created or create new webhook
    logger:
        Which event to subscribe to
    """
    if not logger:
        return "No event specified to subscribe to!"
    if channel.type in {Channel_Types.PUBLIC_THREAD, Channel_Types.PRIVATE_THREAD}:
        channel_id = channel.parent_id
        thread_id = channel.id
    else:
        channel_id = channel.id
        thread_id = None

    token = ""
    if not webhook:
        _webhook: Webhook = await ctx.bot.create_webhook(
            channel_id, "Logger", reason="Subscribing to log event in a new channel"
        )
        webhook = _webhook.id
        token = _webhook.token
    else:
        channel_webhooks = await ctx.bot.get_channel_webhooks(channel_id)
        _webhook = next(
            filter(lambda x: x.id == webhook, channel_webhooks),
            next(filter(lambda x: x.user.id == ctx.bot.user_id, channel_webhooks)),
        )
        token = _webhook.token

    await db.Channel.fetch_or_add(session, id=channel_id, server_id=ctx.guild_id)
    await db.Webhook.fetch_or_add(session, id=webhook, server_id=ctx.guild_id, channel_id=channel_id, token=token)

    session.add(db.Subscription(webhook, thread_id=thread_id, source=f"logging-{logger.lower()}"))
    await session.commit()
    ctx.cache.set_loggers(await ctx.cache.get_subscriptions(session))

    return f"Subscribed to events `{logger}` on webhook {_webhook.name} in {'thread' if thread_id else 'channel'} <#{thread_id or channel_id}>"


@register(Groups.ADMIN, main=logging, private_response=True)
async def unsubscribe(ctx: Context, channel: Channel, subscription: ChannelSubscriptions, *, session: db.Session):
    """
    Unsubscribe Webhook from event logging
    Params
    ------
    channel: guild_text, public_thread, private_thread
        Channel to unsubscribe events from
    logger:
        Which event to unsubscribe from
    """
    if not subscription:
        return "No subscription specified to unsubscribe!"

    sub = await db.Subscription.get(
        session,
        db.Subscription.webhook_id.in_(
            select(db.Webhook.id).where(db.Webhook.server_id == ctx.guild_id, db.Webhook.channel_id == ctx.channel_id)
        ),
        db.Subscription.source == subscription,
    )

    await session.delete(sub)
    await session.commit()
    ctx.cache.set_loggers(await ctx.cache.get_subscriptions(session))

    return f"Unsubscribed event `{subscription}` from {'channel' if channel.type is Channel_Types.GUILD_TEXT else 'thread'} <#{channel.id}>"


@register(group=Groups.ADMIN, main=logging, private_response=True)
async def list_(ctx: Context, *, session: db.Session):
    """
    Display list of subscribed loggers and their respective channels/webhooks
    """
    webhooks = await db.Webhook.filter(session, db.Webhook.server_id == ctx.guild_id)
    subs = []
    for webhook in webhooks:
        sub: db.Subscription
        wh = await ctx.bot.get_webhook(webhook.id)
        for sub in await webhook.awaitable_attrs.subscriptions:
            subs.append(
                f"- `{sub.source}`: <#{sub.thread_id if sub.thread_id else webhook.channel_id}> @ {wh.name} by <@{wh.user.id}>"
            )
    return "\n".join(subs)
