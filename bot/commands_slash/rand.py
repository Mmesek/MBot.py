from MFramework import register, Groups, Context
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


@register(group=Groups.GLOBAL, main=roll)
async def coin(ctx: Context) -> str:
    '''Flips coin'''
    return 'Heads' if random.randint(0, 1) else 'Tails'


@register(group=Groups.GLOBAL, main=roll)
async def quote(ctx: Context) -> str:
    '''Sends random quote'''
    from os import path
    if not path.isfile("data/quotes.json"):
        import requests
        raw = requests.get("https://raw.githubusercontent.com/dwyl/quotes/master/quotes.json")
        with open("data/quotes.json", "wb") as file:
            file.write(raw.content)
    with open("data/quotes.json", "r", newline="", encoding="utf-8") as file:
        import json
        q = json.load(file)
    r = random.SystemRandom().randrange(len(q))
    return '_'+q[r]["text"] + "_\n    ~" + q[r]["author"]


@register(group=Groups.GLOBAL, main=roll)
async def xkcdpassword(ctx: Context) -> str:
    '''Generates random xkcd 936 styled password'''
    import secrets
    # On standard Linux systems, use a convenient dictionary file.
    # Other platforms may need to provide their own word-list.
    with open('/usr/share/dict/words') as f:
        words = [word.strip() for word in f]
        password = ' '.join(secrets.choice(words) for i in range(4))
    return password

@register(group=Groups.GLOBAL, main=roll)
async def ratio(ctx: Context, severity: int = 5):
    '''
    Get Ratioed
    Params
    ------
    severity:
        Severity of the ratio
    '''
    with open('data/ratio.txt','r',newline='\n',encoding='utf-8') as file:
        words = set([i.strip() for i in file.readlines()])
    if severity > len(words):
        severity = len(words)
    elif severity < 1:
        severity = 1
    ratios = " + ".join(random.sample(words, severity))
    if len(ratios) > 2000:
        ratios = ratios[:1990] + f" + ...{len(ratios[1990:])}"
    return ratios
