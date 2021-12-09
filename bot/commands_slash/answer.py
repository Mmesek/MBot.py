from MFramework import register, Groups, Context
from MFramework.commands.cooldowns import cooldown, CacheCooldown

import sqlalchemy as sa
from mlib.database import Base, Timestamp, ID

class Answers_Puzzle(Timestamp, Base):
    user_id: int = sa.Column(sa.BigInteger, primary_key=True)
    key: str = sa.Column(sa.String, primary_key=True)
    puzzle: str = sa.Column(sa.String)
    reward_sent: bool = sa.Column(sa.Boolean, default=False)

class Answers_Wrong(Timestamp, ID, Base):
    user_id: int = sa.Column(sa.BigInteger)
    key: str = sa.Column(sa.String)

class Answers_Registered(Timestamp, ID, Base):
    puzzle: str = sa.Column(sa.String)
    key: str = sa.Column(sa.String)
    value: str = sa.Column(sa.String)
    expire_at = sa.Column(sa.DateTime(True))


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
    normalized_answer = answer.strip().replace(" ","")
    lower_answer = normalized_answer.lower()
    session = ctx.db.sql.session()
    from datetime import datetime
    key = session.query(Answers_Registered).filter(Answers_Registered.value.in_([lower_answer, normalized_answer.upper()]), Answers_Registered.timestamp <= datetime.utcnow()).first()
    if key:
        if key.expire_at and key.expire_at <= datetime.utcnow():
            return f"This answer expired <t:{int(key.expire_at.timestamp())}:R> :("
        _puzzle = key.puzzle
        key = f"{key.puzzle}_{key.key}"
        previous_answer = session.query(Answers_Puzzle).filter(Answers_Puzzle.key==key, Answers_Puzzle.user_id==ctx.user_id).first()
        if previous_answer:
            return f"You've already submited answer to this puzzle <t:{int(previous_answer.timestamp.timestamp())}:R>!"
        pa = Answers_Puzzle(key=key, user_id=ctx.user_id, puzzle=_puzzle)
        session.add(pa)
        session.commit()
        all_answers = session.query(sa.func.count(Answers_Registered.key)).filter(Answers_Registered.puzzle == _puzzle).group_by(Answers_Registered.key).all()
        all_answered = session.query(sa.func.count(Answers_Puzzle.key)).filter(Answers_Puzzle.user_id == ctx.user_id, Answers_Puzzle.puzzle == _puzzle).first()
        remaining = len(all_answers) - all_answered[0]
        if remaining:
            remaining = f"\n\nThere's more to find in this puzzle!"
        else:
            remaining = "\n\nYou have managed to find all possible answers for this puzzle, Congratulations!"
        return "Congratulations, you have solved this puzzle! You'll receive your reward(s) after the event ends (or sooner, it reeally depends) based on first-come first-served basis."+remaining
    session.add(Answers_Wrong(key=answer, user_id=ctx.user_id))
    session.commit()
    return "Sadly, that's not the answer to any of currently released puzzles :( Try again later"
