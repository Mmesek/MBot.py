from datetime import datetime, timezone, timedelta
from MFramework import Context, User, Groups, register, Event, EventBetween, Cooldown
from MFramework.database import alchemy as db

def _t(key, language='en', **kwargs):
    from mlib.localization import tr
    return tr("events.december." + key, language, **kwargs)

@register(group=Groups.GLOBAL)
@Event(month=12)
async def Christmas(ctx: Context):
    '''Christmas Event commands'''
    pass

@register(group=Groups.GLOBAL, main=Christmas)
@Cooldown(hours=2)
async def gift(ctx: Context, user: User, *, language):
    '''Send specified user a gift'''
    if user.id == ctx.user.id:
        return await ctx.reply(_t("cant_send_present_to_yourself", language))
    s = ctx.db.sql.session()

    this_user = db.User.fetch_or_add(s, id=ctx.user_id)

    gift_type = db.types.Item.Gift
    own_present = False

    user_history = db.Log.filter(s, server_id=ctx.guild_id, user_id=user, ByUser=ctx.user.id, type=gift_type).first()

    if user_history is not None:
        return await ctx.reply(_t('present_already_sent', language, timestamp=user_history.Timestamp.strftime("%Y/%m/%d %H:%M")))

    for item in this_user.Items:
        if 'Present' in item.Item.Name and item.Item.Name != 'Golden Present':
            if item.Quantity > 0:
                own_present = True
            break

    if not own_present:
        return await ctx.reply(_t('not_enough_presents', language))

    golden_present = db.Items.by_name(s, "Golden Present")

    last_gift = s.query(db.Log).filter(db.Log.server_id == ctx.guild_id, db.Log.user_id == ctx.user.id, db.Log.type == gift_type).order_by(db.Log.timestamp.desc()).first()
    now = datetime.now(tz=timezone.utc)

    if last_gift is None or (now - last_gift.timestamp) >= timedelta(hours=2):
        target_user = db.User.fetch_or_add(s, id=user)

        gift = db.Inventory(golden_present, 1)
        send_item = db.Inventory(item.Item)
        this_user.transfer(ctx.guild_id, target_user, [send_item], [gift], turn_item=True)
        s.commit()
        await ctx.reply(_t('present_sent_successfully', language))        
    else:
        await ctx.reply(_t('remaining_cooldown', language, cooldown=timedelta(hours=2) - (now - last_gift.Timestamp)))


@register(group=Groups.GLOBAL, main=Christmas)
async def cookie(ctx: Context, user: User, *, language):
    '''Send specified user a cookie'''
    if user.id == ctx.user.id:
        return await ctx.reply(_t("cant_send_cookie_to_yourself", language))

    s = ctx.db.sql.session()

    this_user = db.User.fetch_or_add(s, id=ctx.user_id)
    recipent_user = db.User.fetch_or_add(s, id=user.id)

    inv = db.Inventory(db.Item("Cookie", db.Items.Cookie))
    transaction = this_user.transfer(ctx.guild_id, recipent_user, [inv], remove_item=False)

    s.add(transaction)
    s.commit()
    await ctx.reply(_t('cookie_sent', language))

@register(group=Groups.GLOBAL, main=Christmas)
@EventBetween(after_month=12, before_day=24)
async def advent(ctx: Context, *, language):
    '''Claim today's Advent'''
    s = ctx.db.sql.session()
    this_user = db.User.fetch_or_add(s, id=ctx.user_id)

    today = datetime.now(tz=timezone.utc)
    if today.month != 12 or today.day > 24:
        return await ctx.reply(_t('advent_finished', language))

    advent_type = db.Items.Advent
    _today = datetime(today.year, today.month, today.day, tzinfo=timezone.utc)
    _year = datetime(today.year, 1, 1)
    claimed_total = s.query(db.Log).filter(db.Log.user_id == ctx.user.id, db.Log.type == "Advent", db.Log.timestamp >= _year).all()
    claimed_today = False
    for claimed in claimed_total:
        if claimed.Timestamp >= _today:
            claimed_today = True

    if not claimed_today:
        advent_item = db.Item('Advent', advent_type)
        advent_inventory = db.Inventory(advent_item)
        this_user.claim_items(ctx.guild_id, [advent_inventory])
        s.commit()
        await ctx.reply(_t('advent_claimed_successfully', language, total=len(claimed_total)+1))
    else:
        await ctx.reply(_t('advent_already_claimed', language))

@register(group=Groups.GLOBAL, main=Christmas)
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
    await ctx.send(file=img_str, filename="avatar.png")
