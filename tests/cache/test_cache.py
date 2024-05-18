from MFramework.cache import base, guild

from bot.cache import (
    Cache,
    cache,
    channels,
    database,
    experience,
    responses,
    roles,
    settings,
    voice,
)


def test_cache():
    assert issubclass(
        Cache,
        (
            experience.Experience,
            roles.ReactionRoles,
            roles.PresenceRoles,
            roles.Roles,
            channels.RPG,
            channels.Channels,
            settings.Settings,
            base.Commands,
            cache.Tasks,
            cache.Safety,
            cache.Modmail,
            responses.Responses,
            database.Database,
            base.RuntimeCommands,
            voice.Voice,
            guild.Logging,
            guild.ObjectCollections,
            guild.BotMeta,
            guild.GuildCache,
            base.Base,
            base.BasicCache,
        ),
    )
