from MFramework import register, Groups, Context
from MFramework.commands.cooldowns import cooldown, CacheCooldown
import json
answers = {}

def load_answers():
    global answers
    with open('data/answers.json','r',newline='',encoding='utf-8') as file:
        answers = json.load(file)

load_answers()

def find_answer(normalized: str) -> str:
    for key in answers:
        if normalized in [i.strip().lower().replace(" ","") for i in answers[key]]:
            return key
    return None

import sqlalchemy as sa
from mlib.database import Base, Timestamp, ID

class Answers_Puzzle(Timestamp, Base):
    user_id: int = sa.Column(sa.BigInteger, primary_key=True)
    key: str = sa.Column(sa.String, primary_key=True)
    reward_sent: bool = sa.Column(sa.Boolean, default=False)

class Answers_Wrong(Timestamp, ID, Base):
    user_id: int = sa.Column(sa.BigInteger)
    key: str = sa.Column(sa.String)


@register(group=Groups.GLOBAL, guild=289739584546275339, private_response=True)
@cooldown(hours=1, logic=CacheCooldown)
async def answer(ctx: Context, answer: str) -> str:
    '''
    Got an answer to a puzzle?
    Params
    ------
    answer:
        Your answer
    '''
    normalized_answer = answer.strip().lower().replace(" ","")
    key = find_answer(normalized_answer)
    session = ctx.db.sql.session()
    if key:
        previous_answer = session.query(Answers_Puzzle).filter(Answers_Puzzle.key==key, Answers_Puzzle.user_id==ctx.user_id).first()
        if previous_answer:
            return f"You've already answered to this puzzle <t:{int(previous_answer.timestamp.timestamp())}:R>!"
        pa = Answers_Puzzle(key=key, user_id=ctx.user_id)
        session.add(pa)
        session.commit()
        return "Congratulations, you have solved this puzzle! You'll receive your reward(s) after the event ends (or sooner, it reeally depends) based on first-come first-served basis"
    session.add(Answers_Wrong(key=answer, user_id=ctx.user_id))
    session.commit()
    return "Sadly, that's not the answer to any of currently released puzzles :( Try again later"

@register(group=Groups.SYSTEM, interaction=False)
async def reload_answers(ctx: Context, *, language):
    '''
    Reloads answers file
    '''
    load_answers()