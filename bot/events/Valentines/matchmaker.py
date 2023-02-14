from io import BytesIO
from textwrap import wrap

import aiohttp
import sqlalchemy as sa
from MFramework import Attachment, Context, Embed, Event, Interaction, register
from MFramework.commands.components import Button, Button_Styles, Modal, Row, TextInput
from mlib.colors import buffered_image
from mlib.database import Base
from PIL import Image, ImageDraw, ImageFont

from .general import compatibility, valentines


class Matchmaker(Base):
    guild_id = sa.Column(sa.BigInteger, primary_key=True)
    user_id = sa.Column(sa.BigInteger, primary_key=True)
    description = sa.Column(sa.String)
    avatar_url = sa.Column(sa.String)
    username = sa.Column(sa.String)


class Matchmaker_Matches(Base):
    guild_id = sa.Column(sa.BigInteger, primary_key=True)
    user_id = sa.Column(sa.BigInteger, primary_key=True)
    other_user_id = sa.Column(sa.BigInteger, primary_key=True)
    state = sa.Column(sa.Boolean)


@register(main=valentines)
async def matchmaker():
    """Matchmaking Event commands"""
    pass


class Profile(Modal):
    @classmethod
    async def execute(cls, ctx: Context, data: str, inputs: dict[str, str]):
        session = ctx.db.sql.session()
        session.merge(
            Matchmaker(
                guild_id=ctx.guild_id,
                user_id=ctx.user_id,
                description=inputs.get("About You"),
                avatar_url=ctx.user.get_avatar(),
                username=ctx.user.username,
            )
        )
        session.commit()
        return "Profile updated!"


@register(main=matchmaker, auto_defer=False)
@Event(month=2, day=14)
async def profile(ctx: Context):
    """Modify matchmaking profile"""
    session = ctx.db.sql.session()
    _profile: Matchmaker = (
        session.query(Matchmaker).filter(Matchmaker.guild_id == ctx.guild_id, Matchmaker.user_id == ctx.user_id).first()
    )

    return Profile(
        Row(
            TextInput(
                "About You",
                value=_profile.description if _profile else None,
                placeholder="I'm very [...] and [...], looking for someone who can [...] if you know what I mean.",
                required=True,
                min_length=50,
                max_length=250,
            )
        )
    )


@register(main=matchmaker, private_response=True)
@Event(month=2, day=14)
async def search(ctx: Context):
    """Search for new matches"""
    components = Row(Button("Swipe Left", 0, Button_Styles.DANGER), Button("Swipe Right", 1, Button_Styles.SUCCESS))

    session = ctx.db.sql.session()
    matches: list[Matchmaker] = (
        session.query(Matchmaker).filter(Matchmaker.guild_id == ctx.guild_id, Matchmaker.user_id != ctx.user_id).all()
    )

    for match in matches:
        img = Image.open(f"data/images/sparker_card.png")
        draw = ImageDraw.Draw(img)
        font = ImageFont.truetype("data/fonts/Zeyada-Regular.ttf", size=25)

        captions = wrap(match.description, 50)
        draw.multiline_text(
            (50, 460),
            "\n".join(captions),
            fill=(255, 255, 255),
            font=font,
            align="center",
        )

        font = ImageFont.truetype("data/fonts/Gabriela-Regular.ttf", size=25)
        draw.text(
            (8, 670),
            f"If you think {match.username.upper()} is a MATCH for you",
            fill=(255, 255, 255),
            font=font,
            align="center",
        )
        async with aiohttp.ClientSession() as _session:
            async with _session.get(match.avatar_url) as response:
                avatar = await response.read()
        avatar = Image.open(BytesIO(avatar))
        avatar = avatar.resize((475, 355))
        try:
            img.paste(avatar, (25, 90), avatar)
        except:
            pass

        img_str = buffered_image(img)
        attachment = Attachment(file=img_str, filename=f"{match.username}_sparker_card.png")

        await ctx.reply(content="...", attachments=[attachment])
        await ctx.reply(content="...", components=components)
        try:
            response: Interaction = await ctx.bot.wait_for(
                "interaction_create",
                check=lambda x: x.guild_id == ctx.guild_id
                and x.member.user.id == ctx.user_id
                and x.message
                and x.message.content != "",
                timeout=360,
            )
        except:
            session.commit()
            await ctx.reply("Matchmaker offline. Use the command again!", embeds=[], attachments=[], components=[])
            return
        session.merge(
            Matchmaker_Matches(
                guild_id=ctx.guild_id,
                user_id=ctx.user_id,
                other_user_id=match.user_id,
                state=bool(int(response.data.custom_id.split("-")[-1])),
            )
        )
        await response.update("Searching for new match...", components=[], attachments=[])
    session.commit()
    await ctx.reply("No more matches for now! Check back later!", embeds=[], attachments=[], components=[])


@register(main=matchmaker, private_response=True)
@Event(month=2, day=14)
async def check(ctx: Context):
    """Check who you've matched with"""
    session = ctx.db.sql.session()

    matches = session.query(Matchmaker_Matches).filter(Matchmaker_Matches.guild_id == ctx.guild_id)
    matched_self: list[Matchmaker_Matches] = matches.filter(
        Matchmaker_Matches.user_id == ctx.user_id, Matchmaker_Matches.state == True
    ).all()
    matched_by: list[Matchmaker_Matches] = matches.filter(
        Matchmaker_Matches.other_user_id == ctx.user_id, Matchmaker_Matches.state == True
    ).all()

    matched = {i.user_id for i in matched_by}.intersection({i.other_user_id for i in matched_self})
    matched = [f"<@{i}>" for i in sorted(matched, key=lambda x: compatibility(ctx.user_id, x), reverse=True)]

    return Embed(
        title="You have matched with the following!" if len(matched) else "There's no one here, check back later!",
        description="\n".join(matched),
        color=int("e76f71", 16),
    )
