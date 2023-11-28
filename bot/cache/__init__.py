from MFramework.cache import guild

from MFramework import Bot, Guild

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
    guild.Logging,
):
    def __init__(self, bot: Bot, guild: Guild, **kwargs):
        super().__init__(bot=bot, guild=guild)
