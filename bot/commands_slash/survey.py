import sqlalchemy as sa
import sqlalchemy.orm as orm
from MFramework import Context, Groups, Interaction, register
from MFramework.commands.components import (
    Button,
    Button_Styles,
    Option,
    Row,
    Select,
    TextInput,
    interaction_create,
)
from mlib.database import Base


class Survey(Base):
    id: int = sa.Column(sa.Integer, primary_key=True)
    guild_id: int = sa.Column(sa.BigInteger)
    name: str = sa.Column(sa.String)
    questions: list["Survey_Question"] = orm.relationship("Survey_Question")


class Survey_Question(Base):
    id: int = sa.Column(sa.BigInteger, primary_key=True)
    survey_id = sa.Column(sa.ForeignKey("Survey.id"))
    survey: Survey = orm.relationship("Survey", viewonly=True)
    question = sa.Column(sa.String)
    answer_type = sa.Column(sa.String)
    optional = sa.Column(sa.Boolean)
    available_answers = sa.Column(sa.ARRAY(sa.String), nullable=True)


class Survey_Answer(Base):
    survey_id = sa.Column(sa.ForeignKey("Survey.id"), primary_key=True)
    question_id = sa.Column(sa.ForeignKey("Survey_Question.id"), primary_key=True)
    user_id = sa.Column(sa.BigInteger, primary_key=True)
    multiple_answers = sa.Column(sa.ARRAY(sa.String), nullable=True)
    answer = sa.Column(sa.String, nullable=True)


async def Surveys(interaction: Interaction, current: str) -> list[str]:
    """Lists available surveys"""
    session = interaction._Client.db.sql.session()
    return [
        (i[0], i[0])
        for i in (
            session.query(Survey.name)
            .filter(Survey.guild_id == interaction.guild_id, Survey.name.ilike(f"%{current}%"))
            .distinct()
            .limit(25)
            .all()
        )
    ]


async def Questions(interaction: Interaction, current: str) -> list[str]:
    """Lists available surveys"""
    session = interaction._Client.db.sql.session()
    return [
        (i[0], i[0])
        for i in (
            session.query(Survey_Question.question)
            .filter(
                Survey_Question.survey.has(guild_id=interaction.guild_id),
                Survey_Question.question.ilike(f"%{current}%"),
            )
            .distinct()
            .limit(25)
            .all()
        )
    ]


class Single_Answer(Button):
    private_response = True
    auto_deferred = True

    @classmethod
    async def execute(cls, ctx: Context, data: str):
        user_id, survey_id, question_id, answer = data.split(".")
        s = ctx.db.sql.session()
        s.merge(Survey_Answer(survey_id=survey_id, question_id=question_id, user_id=user_id, answer=answer))

        s.commit()

        return f"You've selected {answer}"


class Select_Answer(Select):
    private_response = True
    auto_deferred = True

    @classmethod
    async def execute(cls, ctx: Context, data: str, values: list[str], not_selected: list[Option]):
        user_id, survey_id, question_id = data.split(".")
        s = ctx.db.sql.session()
        if len(values) == 1:
            s.merge(Survey_Answer(survey_id=survey_id, question_id=question_id, user_id=user_id, answer=values[0]))
        else:
            s.merge(
                Survey_Answer(survey_id=survey_id, question_id=question_id, user_id=user_id, multiple_answers=values)
            )

        s.commit()

        return f"You've selected {', '.join(values)}"


@register()
async def survey():
    pass


@register(group=Groups.GLOBAL, main=survey, private_response=True)
async def answer(ctx: Context, name: Surveys):
    """
    Answer a survey!
    Params
    ------
    name:
        Survey to answer
    """
    session = ctx.db.sql.session()
    _survey: Survey = session.query(Survey).filter(Survey.guild_id == ctx.guild_id).filter(Survey.name == name).first()

    answers: list[Survey_Answer] = (
        session.query(Survey_Answer)
        .filter(Survey_Answer.user_id == ctx.user_id, Survey_Answer.survey_id == _survey.id)
        .all()
    )
    answer_ids = [i.question_id for i in answers]
    await ctx.reply(
        "Hey, thanks for partaking in a survey! You can edit your answers as long as you don't click dismiss message. If you have to take a break, you'll have to use the command again, your answered questions will be saved."
    )

    for x, question in enumerate(_survey.questions, start=1):
        if question.id in answer_ids:
            continue

        if question.answer_type == "multiple_answers":
            max_answers = 25
        else:
            max_answers = 1

        custom_id = f"{ctx.user_id}.{_survey.id}.{question.id}"

        if len(question.available_answers) > 5 or max_answers > 1:
            row = []
            for answer in question.available_answers:
                row.append(Option(answer, answer))
            answers = [
                Select_Answer(
                    *row, custom_id=custom_id, min_values=0 if question.optional else 1, max_values=max_answers
                )
            ]
        else:
            answers = []
            for answer in question.available_answers:
                answers.append(Single_Answer(answer, f"{custom_id}.{answer}", Button_Styles.SECONDARY))

        await ctx.send(f"[{x}/{len(_survey.questions)}] {question.question}", components=Row(*answers), private=True)
        response = await ctx.bot.wait_for(
            "interaction_create",
            check=lambda x: x.guild_id == ctx.guild_id and x.member.user.id == ctx.user_id,
            timeout=360,
        )
        await interaction_create(ctx.bot, response)
    await ctx.send("Thank you for partaking in a survey!", components=[], private=True)


@register(group=Groups.MODERATOR, main=survey)
async def new(ctx: Context, name: str):
    """
    Create new Survey
    Params
    ------
    name:
        Name of the survey
    """
    s = ctx.db.sql.session()
    s.add(Survey(guild_id=ctx.guild_id, name=name))
    s.commit()
    return "Survey created. Use `/survey question` to add question(s) to this survey!"


@register(group=Groups.MODERATOR, main=survey)
async def question(
    ctx: Context,
    name: Surveys,
    question: Questions,
    available_answers: str,
    answer_type: str = "single",
    optional: bool = False,
):
    """
    Add/Modify question to a survey
    Params
    ------
    name:
        Survey to modify
    question:
        Question to add/modify
    available_answers:
        Comma separated list of possible Answers. For integer range specify 1..25 instead (max 25 answers)
    optional:
        Whether this question can be skipped
    answer_type:
        Type of this answer, multiple, single, open etc. #TODO NOT IMPLEMENTED YET
    """
    s = ctx.db.sql.session()
    _survey: Survey = s.query(Survey).filter(Survey.guild_id == ctx.guild_id, Survey.name == name).first()
    _question = (
        s.query(Survey_Question)
        .filter(Survey_Question.survey_id == _survey.id, Survey_Question.question == question)
        .first()
    )
    if not _question:
        _question = Survey_Question(survey_id=_survey.id, question=question)
        result = "added"
    else:
        result = "updated"

    _question.answer_type = answer_type
    _question.optional = optional

    if ".." not in available_answers:
        answers = [i.strip() for i in available_answers.split(",")]
    else:
        start, end = available_answers.split("..")
        answers = [str(i) for i in range(int(start), int(end) + 1)]

    _question.available_answers = answers
    s.merge(_question)
    s.commit()

    return f"Question {result}!"
