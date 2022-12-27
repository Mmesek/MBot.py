import time
from datetime import datetime, timedelta, timezone

import sqlalchemy as sa
from MFramework import Context, Groups, register
from MFramework.commands.components import Button
from mlib.database import ID, Base, Timestamp, TimestampUpdate


class Trivia_Questions(Base, ID):
    trivia = sa.Column(sa.String)
    """Trivia Group this question is part of. If any"""
    question = sa.Column(sa.String)
    """Trivia Question"""
    answers = sa.orm.relationship("Trivia_Answers", back_populates="question")
    """Possible trivia answers"""
    time = sa.Column(sa.Float)
    """Time of waiting for answers on this question"""


class Trivia_Answers(Base, ID):
    question_id = sa.Column(sa.ForeignKey("Trivia_Questions.id"))
    """Question ID this answer is for"""
    question = sa.orm.relationship("Trivia_Questions", back_populates="answers")
    """Trivia Question"""
    answer = sa.Column(sa.String)
    """Possible Trivia Answer"""
    correct = sa.Column(sa.Boolean)
    """Whether it's a correct answer"""


class Trivia_Scores(Base, TimestampUpdate):
    game_id = sa.Column(sa.Integer, primary_key=True)
    """Trivia Game ID for this Score"""
    user_id = sa.Column(sa.BigInteger, primary_key=True)
    """User this score is for"""
    score = sa.Column(sa.Float)
    """Score in game"""


class Poll(Button):
    _max_changes = 1
    """Maximum allowed amount of changing answer"""
    _expire_time = timedelta(days=30)
    """After how long should the value expire from KeyValue storage"""

    @classmethod
    async def execute(cls, ctx: "Context", data: str):
        v = ctx.cache.kv.get(f"{cls.__name__.lower()}.{ctx.message_id}.{ctx.user_id}")
        changed = 0
        if v:
            if v["changed"] >= cls._max_changes:
                return "You can't change your answer more than once!"
            changed += 1
        ctx.cache.kv.store(
            f"{cls.__name__.lower()}.{ctx.message_id}.{ctx.user_id}",
            {"value": data, "timestamp": time.time(), "changed": changed},
            expire_time=cls._expire_time,
        )
        return "Noted!"


class Trivia(Poll):
    """Answer based on Button interactions"""

    _max_changes = 1
    _expire_time = timedelta(minutes=3)


async def trivia_msg():
    """Answer based on user's message/text input"""
    pass


async def trivia_start():
    """Setting up Trivia game"""
    pass


async def trivia_next():
    """Moving on to the next question in game"""
    pass


async def trivia_end():
    """Wrap up of Trivia game"""
    pass
