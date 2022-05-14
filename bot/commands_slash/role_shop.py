import aiohttp, enum

import sqlalchemy as sa
from mlib.database import Base

from MFramework import register, Groups, Context, Attachment, Role, onDispatch, Bot, Guild_Member_Update, User, Emoji
from MFramework.commands.components import TextInput, Button, Row, Button_Styles


class Codes(Base):
    code = sa.Column(sa.String, primary_key=True)
    email = sa.Column(sa.String)
    user_id = sa.Column(sa.BigInteger)
    role_id = sa.Column(sa.BigInteger)


@register(group=Groups.DM, private_response=True, bot=963549809447432292, modal_title="Code redeemtion")
async def redeem(
    ctx: Context,
    order_number: TextInput[1, 100] = "SHOP1234 or 12345678",
    associated_email: TextInput[1, 100] = "email@domain.tld",
) -> str:
    """
    Redeem your code for a role!
    """
    session = ctx.db.sql.session()
    entry = Codes.filter(session, code=order_number.strip().upper(), email=associated_email.strip().lower()).first()

    if not entry:
        return f"HOSS could not verify your information and could not conclude you to be a member of the Liars Club. If you believe your credentials are correct, please use Modmail to place a ticket for assistance.\nOrder Number: {order_number}\nEmail: {associated_email}"
    if entry and entry.user_id and entry.user_id != ctx.user_id:
        return "Another Liars Club member has these credentials, if you are receiving this error and have not redeemed your exclusive Liars Club role, please place a modmail ticket."

    await ctx.bot.add_guild_member_role(
        938233719142121482, ctx.user_id, entry.role_id, f"User used code #{order_number}"
    )

    entry.user_id = ctx.user_id
    session.commit()

    return "HOSS has granted you designation as a member of The Liar's Club."


@register(group=Groups.ADMIN, private_response=True, bot=963549809447432292)
async def add_codes(ctx: Context, codes: Attachment, role: Role) -> str:
    """
    Add new codes to database
    Params
    ------
    codes:
        codes to add
    role:
        Role to award for specified codes
    """
    async with aiohttp.ClientSession() as session:
        async with session.get(codes.url) as response:
            file = await response.read()
    import csv
    from io import StringIO

    file = StringIO(file.decode())
    c = csv.reader(file)
    headers = next(c)
    session = ctx.db.sql.session()
    try:
        _ = [i.lower() for i in headers]
        index = _.index("order_name")
        email_index = _.index("customer_email")
    except ValueError:
        index = 0
        email_index = 1
    i = 0
    for row in c:
        i += 1
        session.merge(Codes(code=row[index].strip().upper(), role_id=role.id, email=row[email_index].strip().lower()))
    session.commit()
    return f"Added {i} row(s) successfully!"


@register(group=Groups.MODERATOR, private_response=True, bot=963549809447432292)
async def retrieve(ctx: Context, order_number: str) -> str:
    """
    Check who redeemed that order number
    Params
    ------
    order_number:
        Order number to check
    """
    session = ctx.db.sql.session()
    entry = Codes.filter(session, code=order_number).first()
    if not entry:
        return "Couldn't find order number"
    elif entry.user_id:
        return f"<@{entry.user_id}>"
    return "Order number found, not claimed"


@register(group=Groups.MODERATOR, private_response=True, bot=963549809447432292)
async def unclaim(ctx: Context, user: User, order_number: str = None) -> str:
    """
    Unclaim code claimed by specified user
    Params
    ------
    user:
        User who's code should be unclaimed
    order_number:
        Specific code to unclaim. Leave empty to unclaim all codes associated with user
    """
    session = ctx.db.sql.session()
    entry = Codes.filter(session, user_id=user.id)

    if order_number:
        entry = [entry.filter(code=order_number).first()]
    else:
        entry = entry.all()

    if not entry:
        return "Couldn't find any codes claimed by specified User"

    for _ in entry:
        _.user_id = None

    session.commit()
    return f"Unclaimed {len(entry)} codes"


@onDispatch(event="guild_member_update")
async def membership_screening_role(self: Bot, data: Guild_Member_Update):
    if data.guild_id == 938233719142121482 and not data.pending and 944654765294497892 not in data.roles:
        await self.add_guild_member_role(
            data.guild_id, data.user.id, 944654765294497892, "User passed membership screening"
        )


class CodeRedeemption(Button):
    auto_deferred: bool = False

    @classmethod
    async def execute(cls, ctx: Context, data: str):
        return redeem


class Button_Types(enum.Enum):
    Primary = Button_Styles.PRIMARY.name
    Secondary = Button_Styles.SECONDARY.name
    Success = Button_Styles.SUCCESS.name
    Danger = Button_Styles.DANGER.name


@register(group=Groups.ADMIN, private_response=True, bot=963549809447432292)
async def make_button(ctx: Context, label: str, style: Button_Types, emoji: str = None, text: str = None):
    """
    Create button that acts like /redeem
    Params
    ------
    label:
        Name of the button
    style:
        Style of button to use
    emoji:
        Emoji to put into the button
    text:
        Optional message before button
    """
    if emoji:
        emoji = emoji.strip("<>").split(":")
        if len(emoji) == 1:
            emoji.append(None)
        emoji = Emoji(id=emoji[-1], name=emoji[-2], animated="a" == emoji[0])
    await ctx.send(
        text,
        components=Row(CodeRedeemption(label=label, emoji=emoji, style=Button_Styles.get(style.value))),
        channel_id=ctx.channel_id,
    )
    return "Message sent!"
