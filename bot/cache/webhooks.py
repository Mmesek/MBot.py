from MFramework.cache.guild import Logging, Webhook

from bot import database as db
from bot.cache.database import Database


class Webhooks(Database, Logging):
    async def get_subscriptions(self, session: db.Session):
        webhooks = await db.Webhook.filter(
            session,
            db.Webhook.server_id == self.guild_id,
            db.Webhook.subscriptions.any(db.Subscription.source.contains("logging-")),
        )
        c = {
            sub.source.replace("logging-", "").replace("_log", ""): Webhook(webhook.id, webhook.token, sub.thread_id)
            for webhook in webhooks
            for sub in (await webhook.awaitable_attrs.subscriptions)
            if "logging-" in sub.source
        }
        return c
