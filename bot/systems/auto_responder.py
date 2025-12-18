import re

from MFramework import onDispatch, Message, Attachment
from bot import Bot, Context


async def responder(ctx: Bot, msg: Message, emoji: str):
    emoji = ctx.cache[msg.guild_id].custom_emojis.get(emoji.lower().strip(":"))
    if type(emoji) is str:
        await msg.reply(emoji)
    elif type(emoji) is tuple:
        await msg.reply(attachments=[Attachment(file=emoji[1], filename=emoji[0])])


SNIPPET_PATTERN = re.compile(r"(?:(?P<cmd>[\D]+?)): ?(?:(?P<args>[^-\n]+)) ?(?:-(?P<flags>[\w]+))?")
# (?:(?P<cmd>[\D]+(?: |:))) ?(?:(?P<args>[^-\n]+)) ?(?:-(?P<flags>[\w]+))?
ALIASES = {"m": "Meme", "r": "Rule", "s": "Snippet"}

EMOJI = re.compile(r":\w+:")


@onDispatch(priority=4)
async def message_create(self: Bot, data: Message):
    if not data.is_empty:
        if any(i.id == self.user_id for i in data.mentions):
            await self.trigger_typing_indicator(data.channel_id)
        for emoji in set(emoji.lower() for emoji in EMOJI.findall(data.content)):
            await responder(self, data, emoji)
        from bot.commands_slash.db import stashed

        snippets = set(SNIPPET_PATTERN.finditer(data.content))
        if snippets:
            ctx = Context(self.cache, self, data)
            r = []
            for snippet in snippets:
                from bot import database as db

                cmd = snippet.group("cmd")
                try:
                    cmd = db.types.Snippet.get(ALIASES.get(cmd.lower(), cmd.title().rstrip("s")))
                except:
                    continue
                if cmd:
                    args = snippet.group("args")
                    search = True if "search" in (snippet.group("flags") or "") else None
                    _ = await stashed(
                        ctx, cmd, args, search, detailed=False, show_all=False, text_only=True, show_content=True
                    )
                    if _:
                        r.append(_)
            if r:
                await ctx.reply("\n".join(r))
