"""
Pythagorean Numerology Calculator
-----------

:copyright: (c) 2024-05 Mmesek
"""

from datetime import datetime
from itertools import cycle
from string import ascii_uppercase as ALPHABETH

from MFramework import Embed, Embed_Field, Groups, register
from mlib.utils import replace_multiple

LETTER_VALUES = dict(zip(ALPHABETH, cycle(range(1, 10))))
VOWEL_VALUES = {"A": 1, "E": 5, "I": 9, "O": 6, "U": 3, "Y": 7}
MASTER_NUMBERS = {11, 22, 33}

EMPTY_FIELD = Embed_Field(name="\u200b", value="\u200b", inline=True)


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
    return Embed(
        fields=[
            Embed_Field(name="Life Path", value=str(path(birth_date)), inline=True) if birth_date else EMPTY_FIELD,
            (
                Embed_Field(
                    name="Heart's Desire/Soul Urge",
                    value=str(desire(full_name)),
                    inline=True,
                )
                if full_name
                else EMPTY_FIELD
            ),
            (
                Embed_Field(
                    name="Expression/Destiny",
                    value=str(expression(full_name)),
                    inline=True,
                )
                if full_name
                else EMPTY_FIELD
            ),
            (
                Embed_Field(
                    name="Personality Number",
                    value=f"Subtraction method: { personality_combined(full_name)}"
                    + f"\nName method: { personality(full_name)}",
                    inline=True,
                )
                if full_name
                else EMPTY_FIELD
            ),
            EMPTY_FIELD,
            (
                Embed_Field(
                    name="Birthday number",
                    value=str(reduce(int(birth_date.split("-")[-1]))),
                    inline=True,
                )
                if birth_date
                else EMPTY_FIELD
            ),
        ]
    )


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
    >>> path("1998-04-14") #(datetime(1998, 4, 14))
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
