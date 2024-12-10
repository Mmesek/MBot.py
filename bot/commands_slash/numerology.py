"""
Pythagorean Numerology Calculator
-----------

:copyright: (c) 2024-05 Mmesek
"""

import json
from collections import Counter
from datetime import datetime
from itertools import cycle
from string import ascii_uppercase as ALPHABETH

from MFramework import Embed, Embed_Field, Groups, register
from mlib.utils import replace_multiple

LETTER_VALUES = dict(zip(ALPHABETH, cycle(range(1, 10))))
LETTER_VALUES.update({"Ą": 1, "Ć": 3, "Ę": 5, "Ń": 5, "Ó": 6, "Ś": 1, "Ź": 8, "Ż": 8, "Ł": 7})
VOWEL_VALUES = {"A": 1, "E": 5, "I": 9, "O": 6, "U": 3, "Y": 7}
MASTER_NUMBERS = {11, 22, 33}

EMPTY_FIELD = Embed_Field(name="\u200b", value="\u200b", inline=True)
with open("data/numerology_traits.json", "r", newline="", encoding="utf-8") as file:
    TRAITS = json.load(file)


def get_title(value: int):
    if value:
        return f"**{TRAITS[str(value)]['title']}**"


def build_description(value: int):
    if value:
        return f"{get_title(value)}: {', '.join(TRAITS[str(value)]['traits'])}"


@register(group=Groups.GLOBAL, private_response=True)
async def numerology(full_name: str, birth_date: str = "") -> Embed:
    """
    Calculate all numbers according to Pythagorean Numerology

    Params
    ------
    full_name:
        Name to use. Y is always treated as a vowel. Substitue with one of value 7 like P if it's not one
    birth_date:
        Birth date to calculate number from. Format: YYYY-MM-DD

    Example
    -------
    >>> import asyncio
    >>> embed = asyncio.run(numerology("Emily Ann Brown", "1998-04-14"))
    >>> [f.value for f in embed.fields]
    ['9', '1', '3', 'Subtraction method: 2\\nName method: 11', '\\u200b', '5']
    """
    _counter = Counter()
    embed = Embed()

    _path = path(birth_date)
    _counter[_path] += 1
    if _path:
        embed.add_field(f"Life Path ({_path})", get_title(_path), True)

    _desire = desire(full_name)
    _counter[_desire] += 1
    if _desire:
        embed.add_field(f"Heart's Desire/Soul Urge ({_desire})", get_title(_desire), True)

    _expression = expression(full_name)
    _counter[_expression] += 1
    if _expression:
        embed.add_field(f"Expression/Destiny ({_expression})", get_title(_expression), True)

    _power = reduce(_path + _expression)
    _counter[_power] += 1
    if _power:
        embed.add_field(f"Power {_power}", get_title(_power), True)

    _active = desire(full_name.split(" ")[0])
    _legacy = desire(full_name.split(" ")[-1])
    _name_str = []
    _counter[_active] += 1
    _counter[_legacy] += 1

    if _active:
        _name_str.append(f"Active: {get_title(_active)}")
    if _legacy and len(full_name.split(" ")) > 1:
        _name_str.append(f"Legacy: {get_title(_legacy)}")

    if _active == _legacy:
        _name_str = [get_title(_active)]
    if _active or _legacy:
        embed.add_field(f"Name Numbers ({_active or 0}/{_legacy or 0})", "\n".join(_name_str), True)

    _personality_c = personality_combined(full_name)
    _personality = personality(full_name)
    _personality_str = []
    _counter[_personality_c or _personality] += 1

    if _personality_c and not _personality:
        _personality_str.append(get_title(_personality_c))
    elif _personality_c:
        _personality_str.append(f"Subtraction method: {get_title(_personality_c)}")
    if _personality and not _personality_c:
        _personality_str.append(get_title(_personality))
    elif _personality:
        _personality_str.append(f"Name method: {get_title(_personality)}")

    if _personality_c == _personality:
        _personality_str = [get_title(_personality)]
    if _personality or _personality_c:
        embed.add_field(f"Personality Number ({_personality_c}/{_personality})", "\n".join(_personality_str), True)

    date = [int(i) for i in birth_date.split("-")]

    _birth_day = reduce(date[-1])
    _birth_month = reduce(date[1])
    _birth_year = reduce(date[0])
    _birth_str = []
    _counter[_birth_day] += 1

    if _birth_day:
        _birth_str.append(f"Day: {get_title(_birth_day)}")
    if _birth_month:
        _birth_str.append(f"Month: {get_title(_birth_month)}")
    if _birth_year:
        _birth_str.append(f"Year: {get_title(_birth_year)}")

    if _birth_day == _birth_month == _birth_year:
        _birth_str = [get_title(_birth_day)]
    embed.add_field(f"Birthday number ({_birth_day}/{_birth_month}/{_birth_year})", "\n".join(_birth_str), True)

    intersection = set()
    for v in [_path, _desire, _expression, _personality, _birth_day]:
        if v:
            intersection.intersection_update(set(TRAITS[str(v)]["traits"]))
    embed.add_field("Number Repeatitions", "\n".join([f"{get_title(k)}: {v}" for k, v in _counter.items() if k]), True)

    return embed


def reduce(number: int) -> int:
    """
    Reduces number according to Pythagorean Numerology

    Parameters
    ----------
    number:
        Number to reduce

    Example
    -------
    >>> reduce(13)
    4
    >>> reduce(137)
    11
    >>> reduce(138)
    3
    """
    separated = [int(i) for i in list(str(number))]
    if len(separated) == 1:
        if separated[0] in MASTER_NUMBERS:
            return separated[0]
    result = sum(separated)
    if result not in MASTER_NUMBERS and result > 9:
        return reduce(result)
    return result


def path(birth_date: str) -> int:
    """Calculate Life Path according to Pythagorean Numerology

    Parameters
    ----------
    birth_date:
        Birth date to calculate number from. Format: YYYY-MM-DD

    Example
    -------
    >>> path("1998-04-14")  # (datetime(1998, 4, 14))
    9
    """
    y, m, d = map(int, birth_date.split("-"))
    date = datetime(y, m, d)
    year = reduce(date.year)
    month = reduce(date.month)
    day = reduce(date.day)
    return reduce(year + month + day)


def desire(name: str) -> int:
    """Calculate Heart's Desire/Soul Urge according to Pythagorean Numerology

    Parameters
    ----------
    full_name:
        Y is always treated as a vowel. Substitue with one of value 7 like P if it's not

    Example
    -------
    >>> desire("Emily Ann Brown")
    1
    """
    value = 0
    for letter in name.replace(" ", "").upper():
        value += VOWEL_VALUES.get(letter, 0)
    return reduce(value)


def expression(name: str) -> int:
    """Calculate Expression/Destiny Number according to Pythagorean Numerology

    Parameters
    ----------
    full_name:
        Full name (including middle ones)

    Example
    -------
    >>> expression("Emily Ann Brown")
    3
    """
    value = 0
    for letter in name.replace(" ", "").upper():
        value += LETTER_VALUES.get(letter, 0)
    return reduce(value)


def personality_combined(name: str) -> int:
    """Calculate Personality using subtraction method according to Pythagorean Numerology

    Parameters
    ----------
    name:
        Y is always treated as a vowel. Substitue with one of value 7 like P if it's not

    Example
    -------
    >>> personality_combined("Emily Ann Brown")
    2
    """
    return reduce(abs(expression(name) - desire(name)))


def personality(name: str) -> int:
    """
    Calculate Personality Number using name method according to Pythagorean Numerology

    Parameters
    ----------
    name:
        Y is always treated as a vowel. Substitue with one of value 7 like P if it's not

    Example
    -------
    >>> personality("David Jones")
    1
    """
    value = 0
    for letter in replace_multiple(name.replace(" ", "").upper(), list(VOWEL_VALUES), ""):
        value += LETTER_VALUES.get(letter, 0)
    return reduce(value)
