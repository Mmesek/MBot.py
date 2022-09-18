from collections import Counter
from datetime import datetime

import sqlalchemy as sa
import sqlalchemy.orm as orm
from MFramework import Context, Groups, Interaction, register
from MFramework.utils.leaderboards import Leaderboard, Leaderboard_Entry
from mlib.database import Base


class Challenge(Base):
    id: int = sa.Column(sa.Integer, primary_key=True)
    guild_id: int = sa.Column(sa.BigInteger)
    name: str = sa.Column(sa.String, nullable=False)
    stage: str = sa.Column(sa.String, nullable=True)
    points: int = sa.Column(sa.Integer, default=1)
    # stages: list["Challenge"] = orm.relationship("Challenge", primaryjoin="Challenge.name")
    scores: list["Challenge_Score"] = orm.relationship("Challenge_Score")

    def __init__(self, guild_id: int, name: str, stage: str = None, points: int = 1):
        self.guild_id = guild_id
        self.name = name
        self.stage = stage
        self.points = points

    def new_stage(self, stage: str, points: int = 1):
        return Challenge(self.guild_id, self.name, stage, points)

    def avg_score(self):
        return sum([i.score for i in self.scores]) / len(self.scores)


class Challenge_Score(Base):
    id: int = sa.Column(sa.Integer, primary_key=True)
    timestamp: datetime = sa.Column(sa.TIMESTAMP(True), server_default=sa.func.now())
    challenge_id: int = sa.Column(sa.ForeignKey("Challenge.id"))
    user_id: int = sa.Column(sa.BigInteger)
    score: float = sa.Column(sa.Float, default=1)


async def Challenges(interaction: Interaction, current: str) -> list[str]:
    """Lists available challenges"""
    session = interaction._Client.db.sql.session()
    return [
        (i[0], i[0])
        for i in (
            session.query(Challenge.name)
            .filter(Challenge.guild_id == interaction.guild_id, Challenge.name.like(f"%{current}%"))
            .distinct()
            .limit(25)
            .all()
        )
    ]


async def Stages(interaction: Interaction, current: str) -> list[str]:
    """Lists available stages"""
    session = interaction._Client.db.sql.session()
    query = session.query(Challenge).filter(
        Challenge.guild_id == interaction.guild_id, Challenge.stage.like(f"%{current}%")
    )

    name = next(filter(lambda x: x.name == "name", interaction.data.options), None)
    if name:
        query = query.filter(Challenge.name.like(f"%{name.value}%"))

    return [(f"{i.name}: {i.stage}" if not name else i.stage, i.stage) for i in (query.distinct().limit(25).all())]


@register(group=Groups.GLOBAL)
async def challenge():
    """
    Base for challenges
    """
    pass


@register(group=Groups.MODERATOR, main=challenge, private_response=True)
async def add(ctx: Context, name: str, stage: str = None, points: int = 1):
    """
    Adds new challenge to list
    Params
    ------
    name:
        Name of challenge
    stage:
        Stage to add
    points:
        Maximum amount of available points
    """
    session = ctx.db.sql.session()

    session.add(Challenge(ctx.guild_id, name, stage, points))
    session.commit()
    return f"Added {name}{': '+ stage if stage else ''} with available Points: {points} successfully!"


@register(group=Groups.GLOBAL, main=challenge)
async def progress(ctx: Context, name: Challenges, stage: Stages = None, score: float = None):
    """
    Updates your Progress in a challenge
    Params
    ------
    name:
        Challenge's name to update
    stage:
        Challenge's stage to update (If any)
    score:
        Your current score in this challenge
    """
    session = ctx.db.sql.session()
    _challenge: Challenge = (
        session.query(Challenge)
        .filter(Challenge.guild_id == ctx.guild_id)
        .filter(Challenge.name == name, Challenge.stage == stage)
        .first()
    )
    if not _challenge:
        return "Couldn't find provided challenge and/or stage"

    current_score: Challenge_Score = (
        session.query(Challenge_Score)
        .filter(Challenge_Score.user_id == ctx.user_id, Challenge_Score.challenge_id == _challenge.id)
        .first()
    )
    if not current_score:
        current_score = Challenge_Score(user_id=ctx.user_id, challenge_id=_challenge.id)
        session.add(current_score)
    current_score.score = score if score is not None and score <= _challenge.points else _challenge.points
    session.commit()
    return f"Score for {_challenge.name}{': '+_challenge.stage if _challenge.stage else ''} updated! Points from this challenge: {current_score.score}"


class Challenge_Row(Leaderboard_Entry):
    def __str__(self) -> str:
        return f"`{self.name}` - {self.value[0]} ({self.value[1]})"


@register(group=Groups.GLOBAL, main=challenge)
async def leaderboard(
    ctx: Context, name: Challenges = None, stage: Stages = None, limit: int = 10, reverse: bool = False
):
    """
    Shows leaderboard of total scores for specified challenge
    Params
    ------
    name:
        Challenge's name to show leaderboard for. Leave empty for highscores
    stage:
        Challenge's stage to display
    limit:
        How many rows to show?
    reverse:
        Show from least to most instead
    """
    session = ctx.db.sql.session()
    challenges: Challenge = session.query(Challenge).filter(Challenge.guild_id == ctx.guild_id)
    if name:
        challenges = challenges.filter(Challenge.name == name)
    if stage:
        challenges = challenges.filter(Challenge.stage == stage)

    if name and stage:
        challenges = [challenges.first()]
    else:
        challenges = challenges.all()

    scores = Counter()
    count = Counter()

    for challenge in challenges:
        for score in session.query(Challenge_Score).filter(Challenge_Score.challenge_id == challenge.id).all():
            scores[score.user_id] += score.score
            count[score.user_id] += 1

    return (
        Leaderboard(
            ctx,
            ctx.user_id,
            [Challenge_Row(ctx, key, (value, count[key])) for key, value in scores.items()],
            limit=limit,
            reverse=reverse,
        )
        .as_embed(f"Leaderboard -{' '+name or ''}{' '+ stage if stage else ''}" if name or stage else "Highscores")
        .set_footer("Nickname - Points (Completed)")
    )


class Highscore(Leaderboard_Entry):
    @property
    def name(self) -> str:
        return self.user_id


@register(group=Groups.GLOBAL, main=challenge)
async def list(ctx: Context, name: Challenges = None, reverse: bool = False):
    """
    Lists available challenges alongside average completion
    Params
    ------
    name:
        Lists stages of this challenge
    reverse:
        List completion rates from least to most instead
    """
    session = ctx.db.sql.session()
    q = session.query(Challenge).filter(Challenge.guild_id == ctx.guild_id)
    if name:
        q = q.filter(Challenge.name == name)
    challenges = q.all()

    if not challenges:
        return "Couldn't find provided challenge"

    total = (
        session.query(sa.func.count(Challenge_Score.user_id.distinct()))
        .filter(Challenge_Score.id.in_([i.id for i in challenges]))
        .first()
    ) or [0]
    per_challenge = {
        k[0]: k[1]
        for k in session.query(Challenge_Score.challenge_id, sa.func.count(Challenge_Score.user_id.distinct()))
        .filter(Challenge_Score.id.in_([i.id for i in challenges]))
        .group_by(Challenge_Score.challenge_id)
        .all()
    }

    rate_challenge = {k: v / total[0] for k, v in per_challenge.items()}

    return Leaderboard(
        ctx,
        ctx.user_id,
        [
            Highscore(
                ctx,
                f"{i.name}{': '+i.stage if i.stage else ''}",
                rate_challenge.get(i.id, 0),
                lambda x: f"{rate_challenge.get(x, 0)*100}%",
            )
            for i in challenges
        ],
        reverse=reverse,
    ).as_embed("Completion rates")
