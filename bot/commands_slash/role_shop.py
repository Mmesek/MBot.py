import aiohttp

import sqlalchemy as sa
from mlib.database import Base

from MFramework import (
    register,
    Groups,
    Context,
    Attachment,
    Role,
    onDispatch,
    Bot,
    Guild_Member_Update,
)
from MFramework.commands.components import Modal, TextInput, Text_Input_Styles, Row


class Codes(Base):
    code = sa.Column(sa.String, primary_key=True)
    email = sa.Column(sa.String)
    user_id = sa.Column(sa.BigInteger)
    role_id = sa.Column(sa.BigInteger)


class Code(Modal):
    @classmethod
    async def execute(cls, ctx: Context, data: str, inputs: dict[str, str]):
        code = inputs.get("Order Number")
        email = inputs.get("Associated Email")

        session = ctx.db.sql.session()
        entry = Codes.filter(session, code=code.strip().upper(), email=email.strip().lower()).first()
        if not entry:
            return f"HOSS could not verify your information and could not conclude you to be a member of the Liars Club. If you believe your credentials are correct, please use Modmail to place a ticket for assistance.\nOrder Number: {code}\nEmail: {email}"
        if entry and entry.user_id and entry.user_id != ctx.user_id:
            return "Another Liars Club member has these credentials, if you are receiving this error and have not redeemed your exclusive Liars Club role, please place a modmail ticket."
        await ctx.bot.add_guild_member_role(938233719142121482, ctx.user_id, entry.role_id, f"User used code #{code}")
        entry.user_id = ctx.user_id
        session.commit()
        return "HOSS has granted you designation as a member of The Liar's Club."


@register(group=Groups.DM, auto_defer=False, bot=963549809447432292)
async def redeem(ctx: Context) -> Code:
    """
    Redeem your code for a role!
    """
    return Code(
        Row(
            TextInput(
                "Order Number",
                style=Text_Input_Styles.Short,
                min_length=1,
                max_length=200,
                required=True,
                placeholder="SHOP1234 or 12345678",
            )
        ),
        Row(
            TextInput(
                "Associated Email",
                style=Text_Input_Styles.Short,
                min_length=1,
                max_length=200,
                required=True,
                placeholder="email@domain.tld",
            )
        ),
        title="Code redeemption",
    )


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


@onDispatch(event="guild_member_update")
async def membership_screening_role(self: Bot, data: Guild_Member_Update):
    if data.guild_id == 938233719142121482 and not data.pending and 944654765294497892 not in data.roles:
        await self.add_guild_member_role(
            data.guild_id, data.user.id, 944654765294497892, "User passed membership screening"
        )
