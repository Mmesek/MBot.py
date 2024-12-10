import csv

import bs4
import httpx
from MFramework import Embed, Embed_Field, Groups, register

NAME_MALE_FILE = "data/names/imiona.csv"
NAME_FEMALE_FILE = "data/names/imiona_zenskie.csv"
SECOND_MALE_FILE = "data/names/drugie_imiona.csv"
SECOND_FEMALE_FILE = "data/names/drugie_imiona_zenskie.csv"
SURNAME_MALE_FILE = "data/names/nazwiska.csv"
SURNAME_FEMALE_FILE = "data/names/nazwiska_zenskie.csv"
EMPTY_FIELD = Embed_Field(name="\u200b", value="\u200b", inline=True)


@register(guild=463433273620824104)
def check_():
    pass


def check(file_: str, n: str, exact: bool = False) -> list[str]:
    """Check csv file for any matching strings in the first field and return list of matching rows
    Params
    ------
    file_:
        File to read
    n:
        String to search for
    exact:
        Whether to only return an exact match
    """
    candidates = []
    with open(file_, "r", newline="", encoding="utf-8") as file:
        c = csv.reader(file)
        for row in c:
            if exact and n.lower() == row[0].lower():
                return row
            elif not exact and n.lower() in row[0].lower():
                candidates.append(row)
    return candidates


@register(group=Groups.GLOBAL, main=check_, private_response=True, guild=463433273620824104)
async def names(name_: str) -> str:
    """Check name in PESEL database
    Params
    ------
    name_:
        name to check
    """
    _names = check(NAME_MALE_FILE, name_)
    return (
        "\n".join(
            [f"{name}: {occurences}" for name, _, occurences in sorted(_names, key=lambda x: int(x[-1]), reverse=True)]
        )
        or "None found"
    )


@register(group=Groups.GLOBAL, main=check_, private_response=True, guild=463433273620824104)
async def name(name_: str):
    """
    Fetch name information
    Params
    ------
    name_:
        Name to fetch
    """
    url = f"https://www.imiona.ovh/{name_}.html"
    async with httpx.AsyncClient() as client:
        r = await client.get(url)
    bs = bs4.BeautifulSoup(r.content)
    main = bs.find("div", id="aboutleft")
    name_day = (
        main.find_all("h2")[1]
        .text.splitlines()[-2]
        .strip(",\t ")
        .replace("XII", "December")
        .replace("XI", "November")
        .replace("IX", "September")
        .replace("X", "October")
        .replace("VIII", "August")
        .replace("VII", "July")
        .replace("VI", "June")
        .replace("V", "May")
        .replace("IV", "April")
        .replace("III", "March")
        .replace("II", "February")
        .replace("I", "January")
    )

    description = main.text.splitlines()[2].strip()
    female_names_friendly = ["- " + i.text.strip().title() for i in main.find_all("ul", id="navlist")[0].find_all("li")]
    male_names_friendly = ["- " + i.text.strip().title() for i in main.find_all("ul", id="navlist")[1].find_all("li")]
    female_names_unfriendly = [
        "- " + i.text.strip().title() for i in main.find_all("ul", id="navlist")[2].find_all("li")
    ]
    male_names_unfriendly = ["- " + i.text.strip().title() for i in main.find_all("ul", id="navlist")[3].find_all("li")]
    positives = ["- " + i.text.strip().title() for i in main.find_all("ul", id="navlist")[4].find_all("li")]
    negatives = ["- " + i.text.strip().title() for i in main.find_all("ul", id="navlist")[5].find_all("li")]
    first_male = check(NAME_MALE_FILE, name_, exact=True)
    first_female = check(NAME_FEMALE_FILE, name_, exact=True)
    second_male = check(SECOND_MALE_FILE, name_, exact=True)
    second_female = check(SECOND_FEMALE_FILE, name_, exact=True)
    last_male = check(SURNAME_MALE_FILE, name_, exact=True)
    last_female = check(SURNAME_FEMALE_FILE, name_, exact=True)
    male_occurences = []
    female_occurences = []
    if first_male:
        male_occurences.append(f"First name: {first_male[-1]}")
    if second_male:
        male_occurences.append(f"Second name: {second_male[-1]}")
    if last_male:
        male_occurences.append(f"Surname: {last_male[-1]}")
    if first_female:
        female_occurences.append(f"First name: {first_female[-1]}")
    if second_female:
        female_occurences.append(f"Second name: {second_female[-1]}")
    if last_female:
        female_occurences.append(f"Surname: {last_female[-1]}")
    e = Embed(
        title=name_,
        description=description,
        fields=[
            Embed_Field(name="Positives", value="\n".join([i for i in positives if i != "- "]), inline=True),
            EMPTY_FIELD,
            Embed_Field(name="Negatives", value="\n".join([i for i in negatives if i != "- "]), inline=True),
            Embed_Field(name="Fitting Female Names", value="\n".join(female_names_friendly), inline=True),
            EMPTY_FIELD,
            Embed_Field(name="Fitting Male Names", value="\n".join(male_names_friendly), inline=True),
            Embed_Field(name="Not Fitting Female Names", value="\n".join(female_names_unfriendly), inline=True),
            EMPTY_FIELD,
            Embed_Field(name="Not Fitting Male Names", value="\n".join(male_names_unfriendly), inline=True),
            (
                Embed_Field(name="Male Occurences", value="\n".join(male_occurences), inline=True)
                if male_occurences
                else EMPTY_FIELD
            ),
            EMPTY_FIELD,
            (
                Embed_Field(name="Female Occurences", value="\n".join(female_occurences), inline=True)
                if female_occurences
                else EMPTY_FIELD
            ),
        ],
    )
    if name_day:
        e.set_footer(text="Namesake day: " + name_day)
    return e


@register(group=Groups.GLOBAL, main=check_, private_response=True, guild=463433273620824104)
async def surname(name_: str, *, exact: bool = False) -> str:
    """
    Check surname in PESEL database
    Params
    ------
    name_:
        Surname to check
    """
    _mnames = check(SURNAME_MALE_FILE, name_, exact)
    _fnames = check(SURNAME_FEMALE_FILE, name_, exact)
    if exact:
        _mnames = [_mnames]
        _fnames = [_fnames]
    e = Embed()
    if _mnames:
        e.add_field(
            "Male Surnames",
            "\n".join(
                [
                    f"{name}: {occurences}"
                    for name, occurences in sorted(_mnames, key=lambda x: int(x[-1]), reverse=True)
                ]
            ),
            True,
        )
    if _fnames:
        e.add_field(
            "Female Surnames",
            "\n".join(
                [
                    f"{name}: {occurences}"
                    for name, occurences in sorted(_fnames, key=lambda x: int(x[-1]), reverse=True)
                ]
            ),
            True,
        )
    return e
