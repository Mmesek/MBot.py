from random import SystemRandom

from MFramework import Groups, User, register

random = SystemRandom()


@register()
async def roll():
    """Random Numbers"""
    pass


@register(group=Groups.GLOBAL, main=roll)
async def chance(statement: str) -> str:
    """Rolls a percentage chance
    Params
    ------
    statement:
        String to roll
    """
    from random import randint, seed

    seed(statement)
    return f"{randint(1, 100)}% chance {'that' if 'is' in statement else 'of'} {statement}"


@register(group=Groups.GLOBAL, main=roll)
async def dice(number: int = 20, times: int = 1) -> str:
    """Rolls a die
    Params
    ------
    number:
        Maximal number dice should have
    times:
        How many dices should be rolled
    """
    return ", ".join([str(number) + ": " + str(random.randrange(int(number)) + 1) for i in range(times)])


@register(group=Groups.GLOBAL, main=roll)
async def ball(question: str = None) -> str:
    """
    Asks 8 ball a question
    Params
    ------
    question:
        Question you seek answer to
    """
    with open("data/words/8ball.json", "r", newline="", encoding="utf-8") as file:
        import json

        ball8 = json.load(file)

    base = [
        ball8["conclusive"]["positive"],
        ball8["conclusive"]["negative"],
        ball8["conclusive"]["uncertain"],
        ball8["swears"],
        ball8["questions"],
        ball8["parts"],
        ball8["conclusive"]["forward"],
        ball8["filler"],
    ]

    if random.random() < 0.5:
        answer = random.choice(base)
        answer = random.choice(answer).strip()
        answer = answer.format(
            negation=random.choice(ball8["negation"]).strip(),
            interpunction=random.choice(ball8["interpuntions"]).strip(),
            conclusive=random.choice(random.choice([i for i in ball8["conclusive"].values()]))
            .strip()
            .format(
                interpunction=random.choice(ball8["interpuntions"]).strip(),
                negation=random.choice(ball8["negation"]).strip(),
                conclusive="",
                person=random.choice(ball8["person"]).strip().capitalize(),
            )
            .strip(),
            _self=random.choice(ball8["self"]).strip(),
            self_is=random.choice(ball8["self_is"]).strip(),
            person=random.choice(ball8["person"]).strip(),
            forward=random.choice(ball8["conclusive"]["forward"] + [""])
            .strip()
            .format(person=random.choice(ball8["person"]).strip())
            .strip(),
        )
        answer = answer.strip()
        if len(answer) > 1 and answer[-1] not in {"!", "?", "."} or len(answer) <= 1:
            answer += random.choice(ball8["interpuntions"]).strip(",")
    else:
        answer = random.choice(ball8["answers"])
    return answer


@register(group=Groups.GLOBAL, main=roll)
async def coin() -> str:
    """Flips coin"""
    return "Heads" if random.randint(0, 1) else "Tails"


@register(group=Groups.GLOBAL, main=roll)
async def quote() -> str:
    """Sends random quote"""
    from os import path

    if not path.isfile("data/words/quotes.json"):
        import requests

        raw = requests.get("https://raw.githubusercontent.com/dwyl/quotes/master/quotes.json")
        with open("data/words/quotes.json", "wb") as file:
            file.write(raw.content)
    with open("data/words/quotes.json", "r", newline="", encoding="utf-8") as file:
        import json

        q = json.load(file)
    r = random.randrange(len(q))
    return "_" + q[r]["text"] + "_\n    ~" + q[r]["author"]


@register(group=Groups.GLOBAL, main=roll, private_response=True)
async def xkcdpassword() -> str:
    """Generates random xkcd 936 styled password"""
    import secrets

    # On standard Linux systems, use a convenient dictionary file.
    # Other platforms may need to provide their own word-list.
    with open("data/words/words") as f:
        words = [word.strip() for word in f]
    return " ".join(secrets.choice(words) for i in range(4))


@register(group=Groups.GLOBAL, main=roll)
async def ratio(severity: int = 5) -> str:
    """
    Get Ratioed
    Params
    ------
    severity:
        Severity of the ratio
    """
    with open("data/words/ratio.txt", "r", newline="\n", encoding="utf-8") as file:
        words = [i.strip() for i in file.readlines()]
    if severity > len(words):
        severity = len(words)
    elif severity < 1:
        severity = 1
    ratios = " + ".join(random.sample(words, severity))
    if len(ratios) > 2000:
        ratios = ratios[:1990] + f" + ...{len(ratios[1990:])}"
    return ratios


@register(group=Groups.GLOBAL, main=roll)
async def spin(terms: str = None, k: int = 1) -> str:
    """
    Pick random word(s) from selection
    Params
    ------
    terms:
        Terms to choose from, split using comma (,). Leave empty for any English word
    k:
        Amount of words to choose.
    """
    if not terms:
        with open("data/words/words") as f:
            terms = f.readlines()
    else:
        terms = terms.split(",")
    return ", ".join(random.sample([i.strip() for i in terms], k))


@register(group=Groups.GLOBAL, main=roll)
async def size(user: User) -> str:
    """
    Check user's size
    Params
    ------
    user:
        User to check
    """
    import random

    random.seed(str(user.id))
    return f"{user.username}: 8{'='*random.randint(0,20)}D"
