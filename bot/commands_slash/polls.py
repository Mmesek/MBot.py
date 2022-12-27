from datetime import datetime, timedelta, timezone

import sqlalchemy as sa
from MFramework import Context, Groups, register
from mlib.database import Base, TimestampUpdate


class Polls(Base, TimestampUpdate):
    user_id = sa.Column(sa.BigInteger, primary_key=True)
    message_id = sa.Column(sa.BigInteger, primary_key=True)
    option = sa.Column(sa.Integer)


from MFramework.commands.components import Button


class Poll(Button):
    @classmethod
    async def execute(self, ctx: Context, data: str):
        s = ctx.db.sql.session()
        vote = s.query(Polls).filter(Polls.message_id == ctx.message_id and Polls.user_id == ctx.user_id).first()
        vote = ctx.cache.kv.get(ctx.message_id)
        if vote:
            vote.option = data
            s.commit()
            return f"Changed your choice to {data}!"
        ctx.cache.kv(f"poll.{ctx.message_id}.{ctx.user_id}", data)
        s.add(Polls(user_id=ctx.user_id, message_id=ctx.message_id, option=data))
        s.commit()
        if datetime.now(timezone.utc) - ctx.data.edited_timestamp > timedelta(minutes=5):
            q = s.query(sa.func.count(Polls.option)).filter(Polls.message_id == ctx.message_id).all()
            total = sum(i for i in q)
            # TODO
            await ctx.data.edit()
        return "Your choice has been noted!"


@register(group=Groups.GLOBAL)
async def poll(ctx: Context, question: str, options: str, duration: timedelta = None, public: bool = True):
    """
    Creates a poll
    Params
    ------
    question:
        Poll's Question
    options:
        Answer Option(s) - Separate multiple with |
    duration:
        Poll's duration
    public:
        Whether the current scores should be visible before end of poll
    """
    answers = [Poll(option=x, label=answer.strip()) for x, answer in enumerate(options.split("|"))]
    await ctx.reply(question, components=answers)
