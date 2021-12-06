from datetime import datetime, timezone, timedelta
from MFramework import Context, User, Groups, register, Event, EventBetween
from MFramework.commands.cooldowns import CacheCooldown, cooldown
from MFramework.commands.decorators import Chance
from ... import database as db

def _t(key, language='en', **kwargs):
    from mlib.localization import tr
    return tr("events.december." + key, language, **kwargs)

@register(group=Groups.GLOBAL)
@Event(month=12)
async def christmas(ctx: Context):
    '''Christmas Event commands'''
    pass

@register(group=Groups.GLOBAL, main=christmas)
@cooldown(hours=2, logic=CacheCooldown)
async def gift(ctx: Context, user: User, *, language) -> str:
    '''Send specified user a gift'''
    if user.id == ctx.user.id:
        return _t("cant_send_present_to_yourself", language)
    s = ctx.db.sql.session()

    this_user = db.User.fetch_or_add(s, id=ctx.user_id)

    gift_type = db.types.Item.Gift
    own_present = False

    #user_history = db.Log.filter(s, server_id=ctx.guild_id, user_id=user, ByUser=ctx.user.id, type=gift_type).first()

    #if user_history is not None:
    #    return await ctx.reply(_t('present_already_sent', language, timestamp=user_history.Timestamp.strftime("%Y/%m/%d %H:%M")))

    for item in this_user.items:
        if 'Presents' == item.item.name and item.item.name != 'Golden Present':
            if item.quantity > 0:
                own_present = True
            break

    if not own_present:
        return _t('not_enough_presents', language)

    golden_present = db.items.Item.by_name(s, "Golden Present")

    last_gift = None# s.query(db.Log).filter(db.Log.server_id == ctx.guild_id, db.Log.user_id == ctx.user.id, db.Log.type == gift_type).order_by(db.Log.timestamp.desc()).first()
    now = datetime.now(tz=timezone.utc)

    if last_gift is None or (now - last_gift.timestamp) >= timedelta(hours=2):
        target_user = db.User.fetch_or_add(s, id=user.id)

        gift = db.Inventory(golden_present, 1)
        send_item = db.Inventory(item.item)
        target_user.claim_items(ctx.guild_id, [gift])
        this_user.remove_item(send_item)
        this_user.claim_items(ctx.guild_id, [db.Inventory(db.items.Item.by_name(s, "Sent Present"))])
        s.commit()
        return _t('present_sent_successfully', language, user=user.username) + "<:gold_gift:917012628310724659>"
    else:
        return _t('remaining_cooldown', language, cooldown=timedelta(hours=2) - (now - last_gift.Timestamp))

@register(group=Groups.GLOBAL, main=christmas)
@cooldown(hours=3, logic=CacheCooldown)
@Chance(50, "You've failed!")
async def steal(ctx: Context, target: User) -> str:
    '''
    Attempt to steal someone else's present! (If they have any)
    Params
    ------
    target:
        User you want to rob
    '''
    if target.id == ctx.user.id:
        return "You can't steal from yourself!"
    s = ctx.db.sql.session()

    target_user = db.User.fetch_or_add(s, id=target.id)
    this_user = db.User.fetch_or_add(s, id=ctx.user_id)
    for item in target_user.items:
        if 'Presents' == item.item.name:
            if item.quantity > 0:
                own_present = True
            break

    if not own_present:
        return "Your target doesn't have any presents left!"
    green_present = db.items.Item.by_name(s, "Green Present")
    gift = db.Inventory(green_present, 1)
    this_user.claim_items(ctx.guild_id, [gift])
    target_user.remove_item(db.Inventory(db.items.Item.fetch_or_add(s, name="Presents")))
    this_user.claim_items(ctx.guild_id, [db.Inventory(db.items.Item.by_name(s, "Stolen Presents"))])
    s.commit()
    return "Congratulations Mr Grinch! You've managed to steal a present! <:rotten_gift:917012629518684230>"

@register(group=Groups.GLOBAL, main=christmas)
async def cookie(ctx: Context, user: User, *, language) -> str:
    '''Send specified user a cookie'''
    if user.id == ctx.user.id:
        return _t("cant_send_cookie_to_yourself", language)

    s = ctx.db.sql.session()

    this_user = db.User.fetch_or_add(s, id=ctx.user_id)
    recipent_user = db.User.fetch_or_add(s, id=user.id)

    inv = db.Inventory(db.items.Item.fetch_or_add(s, name="Cookie", type="Gift"))
    transaction = this_user.transfer(ctx.guild_id, recipent_user, [inv], remove_item=False)

    s.add(transaction)
    s.commit()
    return _t('cookie_sent', language)

@register(group=Groups.GLOBAL, main=christmas)
@EventBetween(after_month=12, before_day=24)
async def advent(ctx: Context, *, language) -> str:
    '''Claim today's Advent'''
    s = ctx.db.sql.session()
    this_user = db.User.fetch_or_add(s, id=ctx.user_id)

    today = datetime.now(tz=timezone.utc)
    if today.month != 12 or today.day > 24:
        return _t('advent_finished', language)

    advent_type = db.items.Items.Advent
    _today = datetime(today.year, today.month, today.day, tzinfo=timezone.utc)
    _year = datetime(today.year, 1, 1)
    claimed_total = s.query(db.Log).filter(db.Log.user_id == ctx.user.id, db.Log.type == "Advent", db.Log.timestamp >= _year).all()
    claimed_today = False
    for claimed in claimed_total:
        if claimed.Timestamp >= _today:
            claimed_today = True

    if not claimed_today:
        advent_item = db.items.Item.fetch_or_add(s, name='Advent', type=advent_type)
        advent_inventory = db.Inventory(advent_item)
        this_user.claim_items(ctx.guild_id, [advent_inventory])
        s.commit()
        return _t('advent_claimed_successfully', language, total=len(claimed_total)+1)
    else:
        return _t('advent_already_claimed', language)

@register(group=Groups.GLOBAL, main=christmas, private_response=True)
async def hat(ctx: Context, user: User):
    '''Adds Santa's hat onto user's avatar'''
    await ctx.deferred()
    from PIL import Image
    from io import BytesIO
    import requests
    fd = requests.get(user.get_avatar()+"?size=2048").content
    img = Image.open(BytesIO(fd))
    hat_image = Image.open("data/santa_hat.png")
    img.paste(hat_image,(img.width-400,0), hat_image)
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = buffered.getvalue()
    await ctx.bot.create_message(ctx.channel_id, file=img_str, filename="avatar.png")
