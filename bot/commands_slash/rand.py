from MFramework import register, Groups, Context, Embed
from random import SystemRandom
random = SystemRandom()

@register()
async def roll(ctx: Context):
    '''Random Numbers'''
    pass

@register(group=Groups.GLOBAL, main=roll)
async def chance(ctx: Context, statement: str) -> str:
    '''Rolls a percentage chance
    Params
    ------
    statement:
        String to roll
    '''
    from random import seed, randint
    seed(statement)
    return f"{randint(1, 100)}% chance {'that' if 'is' in statement else 'of'} {statement}"

@register(group=Groups.GLOBAL, main=roll)
async def dice(ctx: Context, number: int=20, times: int=1) -> str:
    '''Rolls a die
    Params
    ------
    number:
        Maximal number dice should have
    times:
        How many dices should be rolled
    '''
    return ', '.join([str(number) + ": " + str(random.randrange(int(number)) + 1) for i in range(times)])

@register(group=Groups.GLOBAL, main=roll)
async def ball(ctx: Context, question: str = None, *args, language, **kwargs):
    '''
    Asks 8 ball a question
    Params
    ------
    question:
        Question you seek answer to
    '''
    await ctx.deferred(False)
    conclusive = {
        "positive": ["Yes", "Yep", "Yup", "Yeah", "Sure", "Of course", "Indeed", "'course", "Excellent", "Possible", "Likely", "Ok", "I think so"],
        "negative": ["No", "Nope", "Unlikely", "No idea", "I don't think so"],
        "uncertain": ["{negation} going to happen{interpunction}", "{negation} gonna happen{interpunction}", "{negation} ok", "inconclusive", "Answer inconclusive" "404", "I think"],
        "forward": ["ask {person}", "try {person}", "consult {person}"]
    }
    questions = ["May I", "42", "To be or not to be... That is the question", "Why would you ask me that?", "Why?", "Why not?", "Why would you dare me to do it again?", "Why me?", "What's your answer?", "Sorry, what?", "Are you?", "Are you insane?!", "Are u ok?"]
    swears = ["F@#${interpunction} {conclusive}", "H#@%${interpunction} {conclusive}", "S%@#{interpunction} {conclusive}", "Bloody answer"]
    self = ["I", "You", "He", "She", "They", ""]
    self_is = ["I am", "You are", "they are", "she is", "he is", ""]
    negation = ["not", ""]
    parts = ["{_self} should {negation} {forward}", "do {negation} {forward}", "will {negation}", "would {negation}", "{negation} going to", "{negation} sure", "{_self} do {negation} know", "{self_is} {negation} certain", "{_self} know that", "In any circumstances: {conclusive}", "In any case: {conclusive}"]
    person = ["doctor", "specialist", "consultant", "someone else", "creator", "owner", "boss", "again", "me", "later", "psychiatrist","psychologist", "marketer", "PR team", "CEO", "Crane", "yourself", ""]
    filler = ["Sorry", "Cheers", "404", "Mental Breakdown", "On break", "be right back", "answer", ""]
    interpuntions = [".", "...", "!", "?", "?!", "!!!", "??", "...?", "...!", ",", ""]
    base = [conclusive["positive"], conclusive["negative"], conclusive['uncertain'], swears, questions, parts, conclusive["forward"], filler]
    
    answers = [
        "Yes", "Definitly", "Highly likely yes", "Ohhh... yes, definitely", "F@#$ YES!", "Sure", "Brilliant idea!", "Of course!", "Of course", "You should", "Yep", "Yeah", 
        "My reply is no", "My reply is yes", "Yes, indeed", "yes, definitely", "No. Definitely.",
        "No", "Nope", "Highly likely nope", "F@#$ NO!", "Are you insane?!", "Don't count on it", "NO... NO NO NO NO NOOOOO!", "Just f@#$ing no!", 
        "You shouldn't", "You should not",
        "Under any circumstances: No", "December 7th",
        "In any circumstances: Yep!",
        "Possible", "Deniable", "Undeniable", "Agreed", "Disagreed", 
        "It's ok", "It's not ok", "u ok?", "It'll be ok", "It won't be ok", 
        "Thanks for asking, no idea", "Thanks for asking.", 
        "Don't ask me that!", "Do not ask me that!", "DO NOT ASK ME THAT",
        "I don't know", "I do not know", "I don't think so", "Why?",
        "I'm not sure", "Ask again later", "Take left answer", "Take right answer", "Take it", "Leave it", "y?", "u wot", "U WOT?!",
        "I'm not certain", "Please try again later", "Why are you asking me this?",
        "404", "Error. Not an answering machine. Try different protocol", "Answer lies within",
        "Who am I to judge?", "Who am I to answer that question?", "It's not my place to say",
        "Sorry, I'm too drunk right now", "Haha, u wot mate", "Go home, u drunk.", "Fly bird, fly!",
        "I'm sorry. Did you ask something?", "What was the question?", "...Come again?", "Consult a consultant", "Call specialist", "Ask someone else", 
        "Hello, who are you?", "Ask Owner", "Ask Creator", "Ask doctor", "Ask boss",
        "Hey! Check out this awesome cat out!", "Have you seen a doctor?", "Try again.", "Do not cheat", "Try again, but this time do not cheat!",
    ]
    if random.random() < 0.5:
        answer = random.choice(base)
        answer = random.choice(answer).strip()
        answer = answer.format(
            negation = random.choice(negation).strip(),
            interpunction = random.choice(interpuntions).strip(),
            conclusive = random.choice(random.choice([i for i in conclusive.values()])).strip().format(
                interpunction = random.choice(interpuntions).strip(),
                negation = random.choice(negation).strip(),
                conclusive = "",
                person  = random.choice(person).strip().capitalize()
            ).strip(),
            _self = random.choice(self).strip(),
            self_is = random.choice(self_is).strip(),
            person = random.choice(person).strip(),
            forward = random.choice(conclusive["forward"] + [""]).strip().format(
                person  = random.choice(person).strip()
            ).strip(),
        )
        answer = answer.strip()
        if len(answer) > 1 and answer[-1] not in {'!', '?', '.'} or len(answer) <= 1:
            answer += random.choice(interpuntions).strip(',')
    else:
        answer = random.choice(answers)
    await ctx.reply(answer)

from enum import Enum
class Moves(Enum):
    PAPER = 'Rock'
    SCISSORS = 'Paper'
    ROCK = 'Scissors'

@register(group=Groups.GLOBAL, main=roll)
async def rps(ctx: Context, move: Moves) -> str:
    '''
    Plays Rock Paper Scissors!
    Params
    ------
    move:
        Move you want to make
    '''
    bot_move = random.choice(list(Moves))
    if move == bot_move:
        result = "It's a **draw**"
    elif move.name.title() == bot_move.value:
        result = 'You **lost**'
    else:
        result = 'You **won**'
    return f"{ctx.bot.username} plays **{bot_move.name.title()}** against {ctx.user.username}'s **{move.name.title()}**. {result}!"

@register(group=Groups.GLOBAL, main=roll)
async def coin(ctx: Context) -> str:
    '''Flips coin'''
    return 'Heads' if random.randint(0, 1) else 'Tails'

@register(group=Groups.GLOBAL)
async def hangman(ctx: Context, words: str = None, multiplayer: bool=False, rounds: int = 1, lives: int=None, hints: bool=True):
    '''
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
    '''
    if not words:
        with open('/usr/share/dict/words') as f:
            words = [word.strip() for word in f]
    else:
        words = [word.strip() for word in words.split(',')]
    msg = await ctx.reply("...")
    hidden = random.choice(list(words))
    uncovered = set()
    secret = set(hidden.lower())
    steps = range(lives or len(secret))
    missed = []
    wrong = 0
    start_at = 19-steps.stop if steps.stop < 19 else 19
    drawing = '''```
{s7}{s8}{s9}{s10}{s11}
{s6} {s12} {s13}
{s5}{s12}  {s14}
{s4}  {s16}{s15}{s17}
{s3}  {s18} {s19}
{s2}{s1}```'''
    process = {
        's7':'_', 's8':'_','s9':'_','s10':'_', 's11':'_',
        's6':'|', 's13':'|',
        's5':'|', 's12':'/', 's14':'O',
        's4':'|', 's16':'/', 's15':'|', 's17':'\\',
        's3':'|', 's18':'/', 's19':'\\',
        's2':'|', 's1':'_'
    }
    x = 0
    while secret:
    #for x, step in enumerate(steps):
        x += 1
        word = [letter if letter in uncovered else "-" for letter in hidden]
        steps_so_far = {}
        for _step, char in process.items():
            steps_so_far[_step] = char if (wrong + start_at) >= int(_step[1:]) else ' '
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
        last_answer = await ctx.bot.wait_for("message_create",
                                    check = lambda x: 
                                            x.channel_id == ctx.channel_id and 
                                            (x.author.id == ctx.user_id if not multiplayer else True), 
                                    timeout = 360)
        answer = last_answer.content.lower().strip()
        if answer == hidden.lower():
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
        secret = set(hidden.lower()).difference(uncovered)
        if not secret:
            # All letters are known
            break
    await msg.edit(f"The word was `{hidden}`! Took `{x-1}` rounds to guess", embeds=[e])

@register(group=Groups.GLOBAL)
async def wordle(ctx: Context, tries: int = 6, multiplayer: bool = False, hard: bool = False):
    '''
    Worlde game with random words each time
    Params
    ------
    tries:
        Amount of chances you have to guess the word
    multiplayer:
        Whether you want to allow other people in chat to guess as well
    hard:
        Whether new attempt should contain previously guessed letters
    '''
    with open('/usr/share/dict/words') as f:
        words = [word.strip() for word in f if "'" not in word]
    hidden = random.choice(list(words))
    await ctx.reply("Send word of same length as \"mystery word\".\n`*` Means it's a correct letter in correct place, `!` is just correct letter and `-` means wrong letter")
    await ctx.data.send_followup("`"+"-"*len(hidden)+f"` ({len(hidden)})")
    r = 0
    guesses = []
    correct_letters = set()
    for i in range(tries+1):
        r += 1
        answer = await ctx.bot.wait_for("message_create",
                                    check = lambda x: 
                                            x.channel_id == ctx.channel_id and 
                                            len(x.content) == len(hidden) and
                                            x.content in set(words) and
                                            (not hard or (
                                                not correct_letters or 
                                                all(letter in x.content for letter in correct_letters)
                                            )) and
                                            (x.author.id == ctx.user_id if not multiplayer else True), 
                                    timeout = 360)
        if answer.content == hidden:
            await answer.reply(f"You guessed correctly! Took `{r}` rounds to guess")
            break
        positions = []
        for x, letter in enumerate(answer.content.lower().strip()):
            if letter in hidden:
                if hidden[x] == letter:
                    # Correct letter
                    positions.append("*")
                    correct_letters.add(letter)
                else:
                    # Correct letter, wrong place
                    positions.append("!")
            else:
                positions.append("-")
        guess = "".join(positions)
        guesses.append(guess)
        await ctx.data.edit_followup(content="\n".join([f"{x+1}. - `{i}`" for x, i in enumerate(guesses)]))
