from MFramework import Groups, register

from bot.commands_slash.astro import zodiac
from bot.commands_slash.names import name as check_name
from bot.commands_slash.names import surname
from bot.commands_slash.numerology import numerology


@register(group=Groups.GLOBAL, private_response=True, guild=463433273620824104)
async def combined(name: str, birth_date: str, city: str):
    """
    Combined output from zodiac, numerology and name information
    Params
    ------
    name:
        Name to fetch
    birth_date:
        Birth date to calculate number from. Format: YYYY-MM-DD HH:MM
    city:
        City, Country of birthplace
    """
    embeds = [
        await numerology(name, birth_date.split(" ", 1)[0]),
        await zodiac(birth_date, city),
        await check_name(name.split(" ")[0]),
    ]
    if len(name.split(" ")) > 1:
        embeds.append(await surname(name.split(" ")[-1], exact=True))
    return embeds
