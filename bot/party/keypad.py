from MFramework import register, Groups, Context, Emoji, Select_Option, Message, Embed
from MFramework.commands.components import Button, Row
from mlib.utils import grouper
from mlib.database import ASession, Base, ID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import BigInteger, select
from datetime import datetime

# TODO: Add adding codes from website
# TODO: Add button to trigger keypad
# TODO: Add puzzle modal answer


class Clue(ID, Base):
    name: Mapped[str]
    description: Mapped[str]
    url: Mapped[str] = mapped_column(default=None)


class Passcode(Base):
    clue_id: Mapped[int]
    code: Mapped[str] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, default=None, nullable=True)
    claimed: Mapped[datetime] = mapped_column(default=None, nullable=True)


class Key(Button):
    auto_deferred = False

    @classmethod
    async def execute(
        cls,
        ctx: "Context",
        data: str,
        values: list[str] = None,
        not_selected: list[Select_Option] = None,
    ):
        title = ctx.data.message.embeds[0].title
        new_title = title.replace("_", data, 1)
        if "_" not in new_title:
            session: ASession
            async with ctx.db.sql.session() as session:
                code = new_title.split(": ", 1)[1]
                res = await Passcode.get(session, Passcode.code == code, Passcode.claimed.is_(None))
                if res:
                    res.user_id = ctx.user_id
                    res.claimed = datetime.now()
                    clue = await Clue.get(session, Clue.id == res.clue_id)
                    if clue:
                        e = Embed()
                        e.set_title(clue.name)
                        e.set_description(clue.description)
                        if clue.url:
                            e.set_image(clue.url)
                        await ctx.data.update(embeds=[e])

                else:
                    await ctx.data.update("Kod nie został rozponany")
                await session.commit()
        else:
            components = []
            for component_row in ctx.data.message.components:
                for component in component_row.components:  # noqa
                    if component.custom_id.endswith(data):
                        component.disabled = True
                    components.append(component)
            await ctx.data.update(
                embeds=[Embed(new_title)], components=[Row(*group) for group in grouper(components, 3)]
            )


EMOJIS = ["📜", "🪶", "⚔️", "🍻", "🗝️", "🏹", "🛡️", "👑", "🕯"]


@register(group=Groups.GLOBAL, private_response=True)
async def keypad(ctx: Context):
    """
    Generates keypad
    """
    g = grouper([Key("", emoji, emoji=Emoji(name=emoji)) for emoji in EMOJIS], 3)
    return Message(embeds=[Embed(title="Klucz: _ _")], components=[Row(*group) for group in g])


@register(group=Groups.GLOBAL, private_response=True)
async def found_clues(ctx: Context, *, session: ASession):
    """
    Lists clues
    """
    stmt = select(Passcode, Clue).filter(Passcode.user_id == ctx.user_id).filter(Passcode.clue_id == Clue.id)
    result = await session.execute(stmt)
    clues = []
    for r in result.all():
        clues.append(r.t[1].name)
    return "- " + "\n- ".join(clues)
