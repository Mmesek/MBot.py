import asyncio
from datetime import datetime, timezone
from typing import Tuple, Union

from MFramework import (
    Attachment,
    Discord_Paths,
    Embed,
    Guild_Ban_Add,
    Guild_Ban_Remove,
    Message,
    Snowflake,
    User,
)
from MFramework.utils.log import Guild_Member_Update, Log
from mlib.localization import secondsToText

from . import models


class Report(Log):
    username = "User Report Log"


class Infraction(Log):
    username = "Infraction Log"
    _types = {
        "warn": "warned",
        "tempmute": "temporarily muted",
        "mute": "muted",
        "kick": "kicked",
        "tempban": "temporarily banned",
        "ban": "banned",
        "unban": "unbanned",
        "unmute": "unmuted",
        "timeout": "timed out",
    }  # HACK

    async def log(
        self,
        guild_id: Snowflake,
        channel_id: Snowflake,
        message_id: Snowflake,
        moderator: User,
        user_id: Snowflake,
        reason: str,
        type: models.Types,
        duration: int = 0,
        attachments: list[Attachment] = None,
    ) -> Message:
        channel = self.bot.cache[guild_id].channels.get(channel_id)
        channel_name = channel.name if channel else channel_id
        string = f'{moderator.username} [{self._types.get(type.name.lower(), type.name)}](<{Discord_Paths.MessageLink.link.format(guild_id=guild_id, channel_id=channel_id, message_id=message_id)}> "{channel_name}") '
        u = f"[<@{user_id}>"

        try:
            user = self.bot.cache[guild_id].members[user_id].user
            u += f" | {user.username}#{user.discriminator}"
        except:
            pass

        u += "]"
        string += u

        if reason != "":
            string += f' for "{reason}"'

        if duration:
            string += f" (Duration: {secondsToText(duration)})"

        embeds = []

        if attachments is not None:
            for attachment in attachments:
                if len(embeds) == 10:
                    break
                embeds.append(Embed().setImage(attachment.url).setTitle(attachment.filename).embed)

        await self._log(content=string, embeds=embeds)

    async def log_dm(
        self, type: models.Types, guild_id: Snowflake, user_id: Snowflake, reason: str = "", duration: int = None
    ) -> Message:
        s = f"You've been {self._types[type.name.lower()]} in {self.bot.cache[guild_id].guild.name} server"

        if reason != "":
            s += f" for {reason}"

        if duration:
            s += f" ({secondsToText(duration)})"

        return await self._log_dm(user_id, s)


class Infraction_Event(Infraction):
    username = "Infraction Event Log"

    async def log(
        self,
        data: Union[Guild_Ban_Add, Guild_Ban_Remove, Guild_Member_Update],
        type: str,
        reason: str = "",
        by_user: str = "",
    ) -> Message:
        if by_user != "":
            try:
                by_user = self.bot.cache[data.guild_id].members[int(by_user)].user.username
            except:
                pass
            string = f"{by_user} {type} [<@{data.user.id}> | {data.user.username}#{data.user.discriminator}]"
        else:
            string = f"[<@{data.user.id}> | {data.user.username}#{data.user.discriminator}] has been {type}"

        if reason and reason == "Too many infractions":
            s = self.bot.db.sql.session()
            infractions = models.Infraction.filter(s, server_id=self.guild_id, user_id=data.user.id).all()
            if infractions:
                string += " for:\n" + "\n".join([f"- {infraction.reason}" for infraction in infractions])
            else:
                string += f' for "{reason}"'
        elif reason != "" and reason != "Unspecified":
            string += f' for "{reason}"'

        if type == "timed out":
            string += f" until <t:{int(data.communication_disabled_until.timestamp())}>"

        await self._log(string)

    async def get_ban_data(
        self, data: Union[Guild_Ban_Add, Guild_Ban_Remove, Guild_Member_Update], type: models.Types, audit_type: str
    ) -> Tuple[bool, bool]:
        await asyncio.sleep(3)

        audit = await self.bot.get_guild_audit_log(data.guild_id, action_type=audit_type)
        reason = None
        moderator = None

        for obj in audit.audit_log_entries:
            # Try to find ban in Audit Log
            if int(obj.target_id) == data.user.id:
                moderator = obj.user_id
                reason = obj.reason
                break

        if reason is None and type is models.Types.Ban:
            # Fall back to fetching ban manually
            reason = await self.bot.get_guild_ban(data.guild_id, data.user.id)
            reason = reason.reason

        s = self.bot.db.sql.session()
        r = models.Infraction.filter(s, server_id=self.guild_id, user_id=data.user.id, reason=reason, type=type).first()

        if r is None:
            if reason and not "Massbanned by" in reason:
                u = models.User.fetch_or_add(s, id=data.user.id)
                duration = None
                if type is models.Types.Timeout:
                    duration = data.communication_disabled_until - datetime.now(tz=timezone.utc)
                    if duration.total_seconds() < 0:
                        return False, False
                u.add_infraction(data.guild_id, moderator, type, reason, duration)
                s.commit()
            return reason, moderator
        return False, False


class Guild_Ban_Add(Infraction_Event):
    async def log(self, data: Guild_Ban_Add):
        reason, moderator = await self.get_ban_data(data, models.Types.Ban, 22)
        if reason is not False:
            await super().log(data, type="banned", reason=reason, by_user=moderator)


class Guild_Ban_Remove(Infraction_Event):
    async def log(self, data: Guild_Ban_Remove):
        reason, moderator = await self.get_ban_data(data, models.Types.Unban, 23)
        if reason is not False:
            await super().log(data, type="unbanned", reason=reason, by_user=moderator)


class Timeout_Event(Guild_Member_Update, Infraction_Event):
    async def log(self, data: Guild_Member_Update):
        if data.communication_disabled_until and data.communication_disabled_until > datetime.now(timezone.utc):
            reason, moderator = await self.get_ban_data(data, models.Types.Timeout, 24)
            await super().log(data, type="timed out", reason=reason, by_user=moderator)
            await super().log_dm(models.Types.Timeout, data.guild_id, data.user.id, reason)


class Auto_Mod(Infraction):
    pass
