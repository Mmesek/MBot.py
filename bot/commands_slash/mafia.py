from random import SystemRandom

import numpy as np
from MFramework import Context, Groups, Snowflake, register
from MFramework.commands.components import Row, Select, Select_Option

random = SystemRandom()

PLAYERS_STEPS = [4, 8, 16]
CARDS: dict[str, tuple[int, int]] = {"Mafia": (2, 3, 4), "Police": (1, 2, 3)}
SPECIAL = ["Doctor", "Sniper"]
CIVILIAN = "Civilian"

ACTIONS = {"Mafia": "Kill", "Police": "Investigate", "Sniper": "Kill", "Doctor": "Protect"}


def interpolate(n, card_steps: list[int]):
    return int(np.interp(n, PLAYERS_STEPS, card_steps))


def make_deck(players: int):
    cards = []
    for role in SPECIAL:
        cards.append(role)
    for role, card_steps in CARDS.items():
        amount = interpolate(players, card_steps)
        cards.extend([role] * amount)
    cards.extend([CIVILIAN] * (players - len(cards)))
    random.shuffle(cards[:players])
    return cards


def pick_role(cards: list[str]):
    return cards.pop()


@register(group=Groups.GLOBAL)
async def mafia(ctx: Context, parameter: type):
    """
    Description to use with help command
    Params
    ------
    parameter:
        description
    """
    pass


class Mafia:
    players: dict[Snowflake, Context]
    roles: dict[Snowflake, str]

    async def start(self):
        cards = make_deck(len(self.players))
        for user_id, player in self.players.items():
            role = cards.pop()
            self.roles[user_id] = role
            await self.notify_player(player, f"You are playing as `{role}`")

    async def notify_player(self, player: Context, message: str):
        await player.send_followup(
            message,
            components=Row(
                Select(
                    [Select_Option(p.user.username, p.user.id) for p in self.players.values()],
                    placeholder=ACTIONS[self.roles[player.user_id]],
                )
            ),
        )
