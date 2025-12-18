import re
from datetime import timedelta

from MFramework import onDispatch, Message, Embed, Groups, Role, log, Channel, Message_Delete
from MFramework.commands._utils import detect_group
from bot import Bot


@onDispatch(event="message_create", priority=5)
async def deduplicate_messages(self: Bot, data: Message) -> bool:
    c = self.cache[data.guild_id].last_messages

    _g = detect_group(self, data.author.id, data.guild_id, data.member.roles)
    if _g.can_use(Groups.MODERATOR):
        return
    _last_message = c.get(data.channel_id, None)
    if (
        _last_message
        and _last_message[0].content
        and _last_message[0].content == data.content
        and _last_message[0].author.id == data.author.id
        and _last_message[0].attachments == data.attachments
        and _last_message[0].referenced_message == data.referenced_message
    ):
        if len(_last_message) >= self.cache[data.guild_id].allowed_duplicated_messages:
            log.debug('Deleting Message "%s" because of being duplicate', data.content)
            await data.delete(reason="Duplicate Message")
            dm = await self.create_dm(data.author.id)
            try:
                embed = Embed().setDescription(data.content).setTitle("Message").setColor("#d10a2b")
                await self.create_message(
                    dm.id, "Hey, we do not allow sending repeating message in a row!", embeds=[embed]
                )
            except:
                pass
            return True
    else:
        self.cache[data.guild_id].last_messages[data.channel_id] = []
    self.cache[data.guild_id].last_messages[data.channel_id].append(data)  # = data
    return False


@onDispatch(event="message_create", priority=5)
async def deduplicate_across_channels(self: Bot, data: Message) -> bool:
    c = self.cache[data.guild_id].last_messages
    for _msg in c.values():
        if (
            _msg[0].channel_id != data.channel_id
            and _msg[0].content == data.content
            and _msg[0].author.id == data.author.id
            and _msg[0].attachments == data.attachments
            and _msg[0].referenced_message == data.referenced_message
            and data.timestamp - _msg[0].timestamp < timedelta(hours=1)
        ):
            log.debug('Deleting Message "%s" because of being duplicate across channels', data.content)
            await data.delete(reason="Duplicate Message across channels")
            return True
    return False


URL_PATTERN = re.compile(r"https?:\/\/.*\..*")


@onDispatch(event="message_create", priority=4)
async def remove_links(self: Bot, data: Message) -> bool:
    if len(data.member.roles) > 0 and any(
        self.cache[data.guild_id].roles.get(i, Role()).color for i in data.member.roles
    ):  # FIXME?
        return False
    cache = self.cache[data.guild_id]
    if URL_PATTERN.search(data.content):
        violations = cache.msgs_violating_link_filter
        VIOLATIONS_COUNT = 3
        if cache.last_violating_user != data.author.id:
            violations = set()
            cache.last_violating_user = data.author.id
        log.debug('Deleting Message "%s" because of matching URL filter', data.content)
        await data.delete(reason="URL and user doesn't have colored Roles")
        violations.add(data.id)
        dm = await self.create_dm(data.author.id)
        if len(violations) > (VIOLATIONS_COUNT - 1):
            log.debug("Kicking user %s because of amount of msgs violating link filter", data.author.id)
            cache.last_violating_user = None
            try:
                await self.create_message(
                    dm.id,
                    f"You've been kicked from {self.cache[data.guild_id].guild.name} server due to being flagged as hijacked account (You have sent multiple links without having colored role). Feel free to return once you get your account back and/or change password",
                )
            except:
                pass
            await self.remove_guild_member(data.guild_id, data.author.id, "Hijacked account")
            from bot.infractions.models import Types

            await self.cache[data.guild_id].logging["infraction"](
                guild_id=data.guild_id,
                channel_id=data.channel_id,
                message_id=data.id,
                moderator=self.cache[data.guild_id].bot.user,
                user_id=data.author.id,
                reason="Hijacked Account",
                duration=None,
                type=Types.Kick,
            )
            return True
        try:
            embed = Embed().setDescription(data.content).setTitle("Message").setColor("#d10a2b")
            await self.create_message(
                dm.id,
                f"Hey, we do not allow sending links by people without colored role. Be more active to gain colored role before attempting to do so again (Violations before being flagged as hijacked account: {len(violations)}/{VIOLATIONS_COUNT})\n\n**[THIS IS AUTOMATED MESSAGE. NO NEED TO RESPOND** *(Please don't reply to this message)* **]**",
                embeds=[embed],
            )
        except:
            pass
        return True


REPLACE_NOT_APLABETIC = re.compile(r"[^a-zA-Z ]")


@onDispatch(event="message_create", priority=10)
async def blocked_words(self: Bot, data: Message) -> bool:
    BLACKLISTED_WORDS = self.cache[data.guild_id].blacklisted_words
    if BLACKLISTED_WORDS:
        if BLACKLISTED_WORDS.search(REPLACE_NOT_APLABETIC.sub("", data.content)):
            log.debug('Deleting Message "%s" because of matching blocked words filter', data.content)
            await data.delete(reason="Blocked Words")
            return True


SPOILER_PATTERN = re.compile(r"\|\|.*?\|\|")


@onDispatch(event="message_create")
async def delete_non_spoilers(self: Bot, data: Message):
    if (
        self.cache[data.guild_id].cached_roles(data.member.roles).can_use(Groups.ADMIN)
        or self.cache[data.guild_id].guild.owner_id == data.author.id
    ):
        return
    if (
        "spoiler" in self.cache[data.guild_id].channels.get(data.channel_id, Channel()).name
        and "delete" in self.cache[data.guild_id].channels.get(data.channel_id, Channel()).topic
        and (
            not all(attachment.filename.startswith("SPOILER") for attachment in data.attachments)
            or SPOILER_PATTERN.sub("", data.content)
        )
    ):  # FIXME
        await data.delete(reason="Message is not surrounded with spoilers")
        return True


@onDispatch(event="message_create")
async def media_only(self: Bot, data: Message):
    channel: Channel = await self.cache[data.guild_id].channels.get(data.channel_id, None)
    if (
        channel
        and channel.topic
        and ("media-only" in channel.topic.lower() and not (data.attachments or URL_PATTERN.search(data.content)))
    ):
        await data.delete(reason="Message doesn't contain attachment or URL in media-only channel")
        return True


@onDispatch(event="message_create", priority=1)
async def no_commands(self: Bot, data: Message):
    if (
        self.cache[data.guild_id].cached_roles(data.member.roles).can_use(Groups.SUPPORT)
        or self.cache[data.guild_id].guild.owner_id == data.author.id
    ):
        return
    channel: Channel = await self.cache[data.guild_id].channels.get(data.channel_id, None)
    if channel and channel.topic and "commands-disabled" in channel.topic.lower():
        return True


@onDispatch(event="message_delete", priority=1)
async def ghost_ping(self: Bot, data: Message_Delete):
    msg: Message = await self.cache[data.guild_id].messages[f"{data.guild_id}.{data.channel_id}.{data.id}"]
    if msg:
        mentions = ", ".join([f"<@{user.id}>" for user in msg.mentions if user.id != msg.author.id and not user.bot])
        if mentions:
            await self.create_message(
                data.channel_id,
                f"Looking for a Ping? <:ping:517493248529530890> Detected Ghostping of {mentions} by <@{msg.author.id}>",
                allowed_mentions=None,
            )
