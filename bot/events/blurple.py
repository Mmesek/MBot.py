import asyncio

from MFramework import Bot, EventBetween, Message, log, onDispatch

try:
    with open("data/blurple.txt", "r", newline="", encoding="utf-8") as file:
        instructions = [i.strip() for i in file.readlines()]
except:
    log.info("Couldn't find Blurple instructions file")

SUGGESTIONS = 0


@onDispatch(predicate=lambda x: x.content.startswith("p/place") and x.channel_id == 1103050073883029605)
@EventBetween(after_month=5, after_day=6, before_month=5, before_day=14)
async def message_create(self: Bot, data: Message):
    if data.content in instructions:
        try:
            instructions.remove(data.content)
        except ValueError:
            log.debug("Attempted to remove instruction that is no longer in a list!")

        await asyncio.sleep(0.5)
        await data.reply(f"Next command: ```{instructions[0]}```")

        global SUGGESTIONS
        SUGGESTIONS += 1
        if SUGGESTIONS % 5 == 0:
            with open("data/blurple.txt", "w", newline="", encoding="utf-8") as file:
                file.writelines("\n".join(instructions))
