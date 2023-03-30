import asyncio
import json
from random import SystemRandom

from MFramework import Context, Embed, Groups, register

random = SystemRandom()


@register(group=Groups.GLOBAL)
async def game():
    """
    Bot Minigames
    """
    pass


from enum import Enum


class Moves(Enum):
    PAPER = "Rock"
    SCISSORS = "Paper"
    ROCK = "Scissors"


@register(group=Groups.GLOBAL, main=game)
async def rps(ctx: Context, move: Moves) -> str:
    """
    Plays Rock Paper Scissors!
    Params
    ------
    move:
        Move you want to make
    """
    bot_move = random.choice(list(Moves))
    if move == bot_move:
        result = "It's a **draw**"
    elif move.name.title() == bot_move.value:
        result = "You **lost**"
    else:
        result = "You **won**"
    return f"{ctx.bot.username} plays **{bot_move.name.title()}** against {ctx.user.username}'s **{move.name.title()}**. {result}!"


@register(group=Groups.GLOBAL, main=game)
async def hangman(
    ctx: Context, words: str = None, multiplayer: bool = False, rounds: int = 1, lives: int = None, hints: bool = True
):
    """
    Hangman game
    Params
    ------
    words:
        List of words to pick hidden one from for others to guess. Separate with comma
    multiplayer:
        Whether Bot should accept answers from other users
    rounds:
        Amount of rounds using single Hangman (Not implemented yet)
    lives:
        Amount of lives. Default is sum of unique letters in hidden word
    hints:
        Whether Bot should reveal a letter in case of wrong answer
    """
    if not words:
        with open("/usr/share/dict/words") as f:
            words = [word.strip() for word in f if "'" not in word]
    else:
        words = [word.strip() for word in words.split(",")]
    msg = await ctx.reply("...")
    hidden = random.choice(list(words)).lower()
    uncovered = set()
    secret = set(hidden)
    steps = range(lives or len(secret))
    missed = []
    wrong = 0
    start_at = 19 - steps.stop if steps.stop < 19 else 19
    drawing = """```
{s7}{s8}{s9}{s10}{s11}
{s6} {s12} {s13}
{s5}{s12}  {s14}
{s4}  {s16}{s15}{s17}
{s3}  {s18} {s19}
{s2}{s1}```"""
    process = {
        "s7": "_",
        "s8": "_",
        "s9": "_",
        "s10": "_",
        "s11": "_",
        "s6": "|",
        "s13": "|",
        "s5": "|",
        "s12": "/",
        "s14": "O",
        "s4": "|",
        "s16": "/",
        "s15": "|",
        "s17": "\\",
        "s3": "|",
        "s18": "/",
        "s19": "\\",
        "s2": "|",
        "s1": "_",
    }
    x = 0
    while secret:
        # for x, step in enumerate(steps):
        x += 1
        word = [letter if letter in uncovered else "-" for letter in hidden]
        steps_so_far = {}
        for _step, char in process.items():
            steps_so_far[_step] = char if (wrong + start_at) >= int(_step[1:]) else " "
        e = (
            Embed(description=drawing.format(**steps_so_far))
            .setTitle(f'Word: `{"".join(word)}`')
            .setFooter(text=f"Remaining lives: {steps.stop - wrong}")
        )
        if missed:
            e.addField("Missed", " ".join(missed))
        if wrong == steps.stop:
            break
        await msg.edit(embeds=[e])
        last_answer = await ctx.bot.wait_for(
            "message_create",
            check=lambda x: x.channel_id == ctx.channel_id
            and (x.author.id == ctx.user_id if not multiplayer else True),
            timeout=360,
        )
        answer = last_answer.content.lower().strip()
        if answer == hidden:
            # Guessed word
            await last_answer.reply("You won, congratulations")
            break
        elif len(answer) == 1 and answer in secret:
            # Guessed letter
            uncovered.add(answer)
        elif hints and (x % (len(steps) / len(set(hidden))) == 0 and len(secret) != 1 and x > 3):
            # Hint
            uncovered.add(random.choice(list(secret)))
        if answer not in uncovered and answer not in missed:
            # Wrong letter/word
            missed.append(answer)
            wrong += 1
        secret = set(hidden).difference(uncovered)
        if not secret:
            # All letters are known
            break
    await msg.edit(f"The word was `{hidden}`! Took `{x-1}` rounds to guess", embeds=[e])


@register(group=Groups.GLOBAL, main=game)
async def wordle(
    ctx: Context,
    tries: int = 6,
    multiplayer: bool = False,
    official: bool = False,
    day: int = None,
    hard: bool = False,
    accept_invalid: bool = False,
    view_letters: int = 0,
):
    """
    Worlde game with random words each time
    Params
    ------
    tries:
        Amount of chances you have to guess the word
    multiplayer:
        Whether you want to allow other people in chat to guess as well
    official:
        Whether today's word from official list should used instead
    day:
        When using official list, Specific day that should be used instead of today
    hard:
        Whether new attempt should contain previously guessed letters
    accept_invalid:
        Whether not valid words should be accepted and consume try
    view_letters:
        How correct letters should be displayed
        Choices:
            Colors = 0
            Symbols = 1
            Letters = 2
    """
    symbols = view_letters == 1
    if symbols:
        view_letters = False
    if official:
        word_list = "data/words/wordle-official.txt"
    else:
        word_list = "/usr/share/dict/words"
    with open(word_list) as f:
        words = [word.strip() for word in f if "'" not in word]
    if official:
        if not day:
            from datetime import datetime

            day = (datetime.today() - datetime(year=2021, month=6, day=19)).days
        hidden = words[day]
    else:
        hidden = random.choice(list(words))
    await ctx.reply(
        'Send word (only valid words are accepted) of same length as "mystery word".\n`*` Means it\'s a correct letter in correct place\n`!` is just correct letter\n`-` means wrong letter'
    )
    await ctx.data.send_followup("`" + "-" * len(hidden) + f"` ({len(hidden)})")
    r = 0
    guesses = []
    correct_letters = set()
    for i in range(tries + 1):
        r += 1
        try:
            answer = await ctx.bot.wait_for(
                "message_create",
                check=lambda x: x.channel_id == ctx.channel_id
                and len(x.content) == len(hidden)
                and (accept_invalid or x.content.lower() in set(words))
                and (not hard or (not correct_letters or all(letter in x.content for letter in correct_letters)))
                and (x.author.id == ctx.user_id if not multiplayer else True),
                timeout=360,
            )
        except TimeoutError:
            return f"Didn't receive any answer for past 6 minutes! Game ended \=( Correct word was: `{hidden}`"
        positions = []
        for x, letter in enumerate(answer.content.lower().strip()):
            if letter in hidden:
                if hidden[x] == letter:
                    # Correct letter
                    positions.append(f"__{letter}__" if view_letters else "🟩" if not symbols else "*")
                    correct_letters.add(letter)
                else:
                    # Correct letter, wrong place
                    positions.append(f"**{letter}**" if view_letters else "🟨" if not symbols else "!")
            else:
                positions.append("🟥" if not symbols else "-")
        guess = "".join(positions)
        guesses.append(guess)
        attempts = "\n".join([f"{x+1} | {i}" for x, i in enumerate(guesses)])
        if not view_letters:
            attempts = f"```{attempts}```"
        await ctx.data.edit_followup(content=f"{attempts}\nRemaining attempts: {tries-r}")
        if answer.content == hidden:
            await answer.reply(f"You guessed correctly! Took `{r}` rounds to guess")
            return
    return f"Sadly you ran out of attempts! Correct word was: `{hidden}`"


@register(group=Groups.NITRO)
async def hunger_games(ctx: Context, players: str, kill_per_round: int = 2) -> str:
    """
    Start an automated hunger games
    Params
    ------
    players:
        List of players. Separate with comma
    kill_per_round:
        How many kills should be in each round
    """
    _players = [i.strip() for i in players.split(",")]

    with open("data/dlhg.json", "r", newline="", encoding="utf-8") as file:
        theme = json.load(file)

    await ctx.reply(f"Let the games begin! {len(_players)} players")
    _round = 0

    while len(_players) > 1:
        _round += 1
        result = []

        for player in random.choices(_players, k=kill_per_round):
            result.append(player + " " + random.choice(theme["dead"]))
            _players.remove(player)

            if len(_players) == 1 and random.randint(1, 3) <= 2:
                break

        for player in _players:
            _result: str = random.choice(theme[random.choice(["alive", "wounded", "team"])])

            result.append(f"**{player}** {_result.format(random.choice([i for i in _players if i != player]))}")

        message = await ctx.data.send_followup(f"Round **{_round}**")
        if message:
            for msg in result:
                await message.edit(message.content + "\n\n" + msg)
                await asyncio.sleep(3)

    await ctx.data.send_followup((", ".join(_players) + " Wins!") if _players else "Everyone's dead. No winners.")
