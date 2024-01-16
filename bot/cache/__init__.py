from MFramework import Bot
from MFramework import Cache as DefaultCache
from MFramework import Guild

from . import cache, channels, experience, responses, roles, settings, voice


class Cache(
    experience.Experience,
    roles.ReactionRoles,
    roles.PresenceRoles,
    channels.RPG,
    settings.Settings,
    cache.Tasks,
    cache.Safety,
    cache.Modmail,
    responses.Responses,
    voice.Voice,
    DefaultCache,
):
    def __init__(self, bot: Bot, guild: Guild, **kwargs):
        super().__init__(bot=bot, guild=guild)
