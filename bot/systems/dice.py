import re
from random import SystemRandom as random

from MFramework import onDispatch, Message
from bot import Bot


ILLEGAL_ACTIONS = re.compile(r"(?i)zabij|wyryw|mord")
DICE_REACTIONS = ["0️⃣", "1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣"]
DICE_EMOJIS = {
    0: "dice_0:761760091648294942",
    1: "dice_1:761760091971780628",
    2: "dice_2:761760091837825075",
    3: "dice_3:761760092206792750",
    4: "dice_4:761760092767911967",
    5: "dice_5:761760093435068446",
    6: "dice_6:761760093817143345",
}


ACTION = re.compile(r"(?:(?=\*)(?<!\*).+?(?!\*\*)(?=\*))")


@onDispatch(event="message_create")
async def roll_dice(self: Bot, data: Message, updated: bool = False):
    channel = self.cache[data.guild_id].threads.get(data.channel_id, data.channel_id)
    if channel not in self.cache[data.guild_id].rpg_channels:
        return
    if updated:
        m = await self.get_channel_message(data.channel_id, data.id)
        if m.reactions:
            return
    reg = ACTION.findall(data.content)
    if reg and set(reg) != {"*"}:
        if "*" in reg:
            reg = set(reg)
            reg.remove("*")
            reg = list(reg)
        dices = self.cache[data.guild_id].rpg_dices or DICE_REACTIONS

        v = random().randint(1, 6) if not ILLEGAL_ACTIONS.findall(reg[0]) else 0
        await self.create_reaction(data.channel_id, data.id, dices[v])
