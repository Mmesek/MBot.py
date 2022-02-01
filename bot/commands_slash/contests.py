import sqlalchemy as sa
from mlib.database import Base

from MFramework import register, Groups, Context, Embed

class Contest_Entries(Base):
    id = sa.Column(sa.BigInteger, primary_key=True)
    msg = sa.Column(sa.BigInteger)
    cc = sa.Column(sa.String)

@register(group=Groups.GLOBAL, guild=289739584546275339, private_response=True)
async def msi(ctx: Context, country: str, text: str = None, attachment: str = None, attachment2: str = None) -> str:
    '''
    Participate in MSI contest
    Params
    ------
    country:
        Country where you live
    text:
        Contest Entry (Up to 500 words) Leave empty, you can fill it in next message
    attachment:
        DIRECT URL to a picture. Must end with either .png or .gif
    attachment2:
        DIRECT URL to a picture 2. Must end with either .png or .gif
    '''
    import pycountry, asyncio
    try:
        _country = pycountry.countries.search_fuzzy(country)
    except:
        return "There was an error searching for provided country, make sure it's as close as possible to actual name and use the command again."
    if _country[0].name.lower() != country.lower():
        await ctx.reply(f"Most similiar Country: {_country[0].name}")
        await asyncio.sleep(5)
    session = ctx.db.sql.session()
    #if Contest_Entries.filter(session, id=ctx.user_id).all():
    #    return "You've already sent your entry!"
    if text and len(text.split(" ")) > 500:
        return "Sadly your entry is too long \=("
    if not text:
        await ctx.reply("Send your entry here (Up to 500 words)")
        try:
            msg = await ctx.bot.wait_for("message_create",
                            check = lambda x: 
                                x.channel_id == ctx.channel_id and 
                                x.content and len(x.content.split(" ")) <= 500 and
                                x.author.id == ctx.user_id,
                            timeout = 600)
        except:
            return "Sadly you didn't respond in time! Use the command again!"
        await msg.delete()
        text = msg.content
    if attachment and not (attachment.endswith(".png") or attachment.endswith(".jpg") or attachment.endswith(".jpeg")) or not attachment.startswith("http"):
        return "Your URL should point directly to an image, not an album!"
    if attachment2 and not (attachment2.endswith(".png") or attachment2.endswith(".jpg") or attachment2.endswith(".jpeg")) or not attachment2.startswith("http"):
        return "Your URL should point directly to an image, not an album!"
    embeds = [Embed().setDescription(text).setImage(attachment).setAuthor(str(ctx.user), icon_url=ctx.user.get_avatar()).setColor("#060606")]
    if attachment2:
        embeds.append(Embed().setImage(attachment2).setColor("#ed1c24"))
    entry = Contest_Entries.filter(session, id=ctx.user_id).first()
    if entry:
        try:
            await ctx.bot.edit_message(934134541487050762, entry.msg, embeds=embeds)
            return "Entry Edited!"
        except:
            pass
    msg = await ctx.bot.create_message(934134541487050762, embeds=embeds)
    session.add(Contest_Entries(id=ctx.user_id, msg=msg.id, cc=_country[0].name))
    session.commit()
    return "Entry Confirmed!"
