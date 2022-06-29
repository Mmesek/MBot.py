import asyncio
from random import SystemRandom

random = SystemRandom()

from MFramework import Bot, Event, Message, onDispatch


def load_responses():
    import json

    with open("data/chicken.json", "r", newline="", encoding="utf-8") as file:
        return json.load(file)


RESPONSES = load_responses()


@onDispatch
@Event(month=4, day=1)
async def message_create(self: Bot, data: Message):
    if any(i.id == self.user_id for i in data.mentions):
        r = random.choices(list(RESPONSES.keys()), list(RESPONSES.values()))[0]
        await asyncio.sleep(1.3)
        await data.reply(
            r.format(
                a1="a" * random.randint(1, 2),
                a2="a" * random.randint(1, 4),
                a3="a" * random.randint(3, 5),
                u1="u" * random.randint(1, 3),
                u2="u" * random.randint(1, 3),
                u3="u" * random.randint(1, 3),
                o1="o" * random.randint(1, 4),
                o2="o" * random.randint(1, 4),
                o3="o" * random.randint(1, 4),
            )
            + ("!" if random.randint(0, 1) else ".")
        )
