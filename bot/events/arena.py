import asyncio
from datetime import datetime, timedelta, timezone
from random import SystemRandom as random

import sqlalchemy as sa
import sqlalchemy.orm as orm
from MFramework import (
    Bot,
    Chance,
    Context,
    Embed,
    Emoji,
    EventBetween,
    Groups,
    Message,
    UserID,
    onDispatch,
    register,
)
from MFramework.commands.components import Button, Modal, Row, TextInput
from MFramework.utils.leaderboards import Leaderboard, Leaderboard_Entry
from mlib.database import Base


class NotAvailable(Exception):
    pass


class Cooldown(NotAvailable):
    pass


class Gladiator(Base):
    id: int = sa.Column(sa.Integer, primary_key=True)
    guild_id: int = sa.Column(sa.BigInteger)
    user_id: int = sa.Column(sa.BigInteger)
    history: list["Gladiator_History"] = orm.relationship("Gladiator_History")

    def bonus(self, boss: "Gladiator_Boss") -> int:
        return sum(
            [
                i.bonus
                for i in self.history
                if i.timestamp <= boss.ends_at and i.timestamp >= boss.start_at and i.guild_id == boss.guild_id
            ]
        )

    def damage_dealt(self, boss: "Gladiator_Boss") -> int:
        return sum([i.damage for i in self.history if i.boss_id == boss.id])

    def total_damage(self, guild_id: int) -> int:
        return sum([i.bonus for i in self.history if i.guild_id == guild_id])

    def add_bonus(self, bonus: int) -> None:
        self.history.append(Gladiator_History(bonus=bonus, user_id=self.user_id, guild_id=self.guild_id))

    def add_attack(self, boss: "Gladiator_Boss") -> int:
        damage = 1 + self.bonus(boss)
        damage = damage if damage <= boss.health else boss.health
        boss.health -= damage
        self.history.append(
            Gladiator_History(damage=damage, boss_id=boss.id, user_id=self.user_id, guild_id=self.guild_id)
        )
        return damage


class Gladiator_History(Base):
    id: int = sa.Column(sa.Integer, primary_key=True)
    user_id: int = sa.Column(sa.BigInteger)
    guild_id: int = sa.Column(sa.BigInteger)
    gladiator_id: int = sa.Column(sa.ForeignKey("Gladiator.id"))
    boss_id: int = sa.Column(sa.ForeignKey("Gladiator_Boss.id"))
    damage: int = sa.Column(sa.Integer, default=0)
    bonus: int = sa.Column(sa.Integer, default=0)
    timestamp: datetime = sa.Column(sa.TIMESTAMP(True), server_default=sa.func.now())

    @classmethod
    async def list(cls, ctx: Context, min_damage: int = 1, *, session=None) -> list:
        """
        Lists users that dealt any damage
        Params
        ------
        min_damage:
            minimum damage user dealt
        """
        if not session:
            session = ctx.db.sql.session()
        u: list[Gladiator_History] = (
            session.query(Gladiator_History.user_id, sa.func.sum(Gladiator_History.damage))
            .filter(Gladiator_History.guild_id == ctx.guild_id)
            .group_by(Gladiator_History.user_id)
            .order_by(sa.func.sum(Gladiator_History.damage))
            .all()
        )
        return [i for i in u if i[1] >= min_damage]


class Gladiator_Boss(Base):
    id: int = sa.Column(sa.Integer, primary_key=True)
    guild_id: int = sa.Column(sa.BigInteger)
    health: int = sa.Column(sa.Integer, nullable=False)
    name: str = sa.Column(sa.String, nullable=False)
    start_at: datetime = sa.Column(sa.TIMESTAMP(True), server_default=sa.func.now())
    ends_at: datetime = sa.Column(sa.TIMESTAMP(True), nullable=False)
    image_url: str = sa.Column(sa.String)

    def attack(self, session, user_id: int) -> int:
        now = datetime.now(tz=timezone.utc)

        if now > self.ends_at:
            raise NotAvailable(f"{self.name} is not available anymore!")
        elif self.health <= 0:
            raise NotAvailable(f"{self.name} has already been slain!")

        player = (
            session.query(Gladiator).filter(Gladiator.user_id == user_id, Gladiator.guild_id == self.guild_id).first()
        )
        if not player:
            player = Gladiator(user_id=user_id, guild_id=self.guild_id)
            session.add(player)

        history = [i for i in player.history if i.damage]

        if history:
            remaining_cooldown = timedelta(minutes=30) - (now - history[-1].timestamp)
        else:
            remaining_cooldown = timedelta()

        if remaining_cooldown.total_seconds() > 0:
            raise Cooldown(f"Cooldown remaining: <t:{int((now + remaining_cooldown).timestamp())}:R>")

        return player.add_attack(self)

    async def spawn(self: "Gladiator_Boss", bot: Bot, data: Message, *, _wait: int = 60):
        t = int((datetime.now(timezone.utc) + timedelta(seconds=_wait)).timestamp())
        embed = (
            Embed()
            .set_image(self.image_url)
            .set_title(self.name)
            .set_description("Your chatting attracted some fighters looking for a fight!")
            .add_field("Fighter will flee in", f"<t:{t}:R>")
        )
        components = Row(Attack(f"Attack {self.name}", custom_id=f"{self.name}-{t}", emoji=Emoji(id=None, name="⚔")))

        msg = await bot.create_message(data.channel_id, embeds=[embed], components=components)
        await asyncio.sleep(_wait or 60)
        await bot.delete_message(msg.channel_id, msg.id)

    @classmethod
    async def bonus(cls: "Gladiator_Boss", bot: Bot, data: Message, *, _wait: int = 60):
        _bonus = random().randint(1, 5)
        if not _wait:
            _wait = random().randint(5, 60)
        t = int((datetime.now(timezone.utc) + timedelta(seconds=_wait)).timestamp())
        components = Row(Bonus(f"+{_bonus} damage", f"{_bonus}-{t}", emoji=Emoji(name="✨", id=None)))

        msg = await bot.create_message(
            data.channel_id,
            content=f"While chatting, you find something to sharpen your weapon! (+{_bonus} damage). All out <t:{t}:R>",
            components=components,
        )
        await asyncio.sleep(_wait)
        await bot.delete_message(msg.channel_id, msg.id)
        return True

    @classmethod
    def get(cls, session, ctx: Context, name: str = None) -> "Gladiator_Boss":
        now = datetime.now(timezone.utc)
        boss = (
            session.query(Gladiator_Boss)
            .filter(Gladiator_Boss.guild_id == ctx.guild_id)
            .filter(Gladiator_Boss.health > 0)
            .filter(Gladiator_Boss.ends_at >= now)
            .filter(Gladiator_Boss.start_at <= now)
            .order_by(sa.func.random())
        )

        if name:
            boss = boss.filter(Gladiator_Boss.name == name)

        boss = boss.first()

        if not boss:
            raise NotAvailable("Couldn't find such Fighter")
        return boss


@register()
async def arena():
    pass


@register(main=arena)
async def manage():
    pass


@register(main=manage, private_response=True)
async def create(ctx: Context, name: str, health: int, duration: timedelta, image: str = None) -> str:
    """
    Create new boss
    Params
    ------
    name:
        Name of the boss
    health:
        Starting health of a boss
    duration:
        How long the boss should be active
    image:
        URL to an image of the boss
    """
    s = ctx.db.sql.session()

    if Gladiator_Boss.filter(s, name=name, guild_id=ctx.guild_id).first():
        return "Fighter already exists"

    s.add(
        Gladiator_Boss(
            name=name,
            health=health,
            ends_at=ctx.data.id.as_date.astimezone(timezone.utc) + duration,
            guild_id=ctx.guild_id,
            image_url=image,
        )
    )
    s.commit()

    return "Success"


@register(group=Groups.ADMIN, main=manage)
async def attack(ctx: Context, name: str = None, *, user_id: UserID = None, session=None) -> str:
    """
    Attacks boss
    Params
    ------
    name:
        Boss to attack
    user_id:
        User that should perform the attack
    """
    if not session:
        session = ctx.db.sql.session()

    boss = Gladiator_Boss.get(session, ctx, name)

    dmg = boss.attack(session, user_id or ctx.user_id)
    session.commit()

    return f"Dealt {dmg} to {boss.name}"


@register(group=Groups.MODERATOR, main=manage)
async def bonus(ctx: Context, bonus: int, *, user_id: UserID = None, session=None) -> int:
    """
    Adds damage bonus
    Params
    ------
    bonus:
        bonus to add
    user_id:
        User that should receive the bonus
    """
    if not session:
        session = ctx.db.sql.session()

    player = (
        session.query(Gladiator)
        .filter(Gladiator.user_id == (user_id or ctx.user_id))
        .filter(Gladiator.guild_id == ctx.guild_id)
        .first()
    )

    if not player:
        player = Gladiator(user_id=user_id or ctx.user_id, guild_id=ctx.guild_id)
        session.add(player)

    history = [
        i for i in player.history if i.timestamp >= (datetime.now(timezone.utc) - timedelta(minutes=1)) and i.bonus
    ]
    if not history:
        player.add_bonus(bonus)
        session.commit()
    else:
        raise NotAvailable("Sorry, you've already claimed a damage bonus recently!")

    return player.bonus(Gladiator_Boss.get(session, ctx))


@register(group=Groups.GLOBAL, main=arena)
async def stats():
    pass


@register(group=Groups.GLOBAL, main=stats, private_response=True)
async def boss(ctx: Context, name: str = None) -> int:
    """
    Checks remaining boss's health
    Params
    ------
    name:
        Name of the boss to check
    """
    with ctx.db.sql.session() as session:
        boss = Gladiator_Boss.get(session, ctx, name)

    return boss.health


@register(group=Groups.GLOBAL, main=stats, private_response=True)
async def user(ctx: Context, user_id: UserID = None, *, session=None) -> Embed:
    """
    Shows player stats
    Params
    ------
    user_id:
        user to show
    """
    if not session:
        session = ctx.db.sql.session()
    player: Gladiator = (
        session.query(Gladiator)
        .filter(Gladiator.user_id == (user_id or ctx.user_id), Gladiator.guild_id == ctx.guild_id)
        .first()
    )
    if not player:
        return "No stats"
    embed = Embed()
    embed.add_field("Current damage bonus", str(player.bonus(Gladiator_Boss.get(session, ctx))), True)
    if player.history:
        embed.add_field("Total damage dealt", str(sum([i.damage for i in player.history])), True)
        embed.add_field("Last attack", f"<t:{int(player.history[-1].timestamp.timestamp())}:R>", True)
        remaining_cooldown: timedelta = timedelta(minutes=30) - (
            datetime.now(tz=timezone.utc) - player.history[-1].timestamp
        )
        if remaining_cooldown.total_seconds() > 0:
            embed.add_field(
                "Cooldown remaining",
                f"<t:{int((datetime.now(tz=timezone.utc) + remaining_cooldown).timestamp())}:R>",
                True,
            )
    return embed


@register(group=Groups.GLOBAL, main=stats, private_response=True)
async def leaderboard(ctx: Context) -> Embed:
    """
    Shows leaderboards
    """
    return Leaderboard(
        ctx, ctx.user_id, [Leaderboard_Entry(ctx, i[0], i[1]) for i in await Gladiator_History.list(ctx)]
    ).as_embed()


@register(group=Groups.GLOBAL, main=stats, private_response=True)
async def bosses(ctx: Context) -> str:
    """
    Shows list of boss's and their stats
    """
    session = ctx.db.sql.session()
    bosses: list[Gladiator_Boss] = (
        session.query(Gladiator_Boss)
        .filter(Gladiator_Boss.guild_id == ctx.guild_id)
        .order_by(Gladiator_Boss.ends_at)
        .all()
    )
    return "\n".join([f"{boss.name} - {boss.health} | <t:{int(boss.ends_at.timestamp())}:R>" for boss in bosses])


class Attack(Button):
    private_response = True
    auto_deferred: bool = True

    @classmethod
    async def execute(cls, ctx: Context, data: str):
        data, t = data.split("-")
        if datetime.fromtimestamp(int(t)) <= datetime.now():
            return "Fighter has already fled from this fight!"
        try:
            return await attack(ctx, data)
        except NotAvailable as ex:
            return ex


@onDispatch(event="message_create")
@EventBetween(after_month=8, before_month=10, before_day=13)
@Chance(3)
async def spawn_fighter(bot: Bot, data: Message):
    with bot.db.sql.session() as session:
        try:
            boss = Gladiator_Boss.get(session, data)
        except NotAvailable:
            return
    await boss.spawn(bot, data)


class Bonus(Button):
    private_response = True
    auto_deferred: bool = True

    @classmethod
    async def execute(cls, ctx: Context, data: str):
        data, t = data.split("-")
        if datetime.fromtimestamp(int(t)) <= datetime.now():
            return "This bonus is already expired!"
        try:
            return f"Current bonus: {await bonus(ctx, int(data))}"
        except NotAvailable as ex:
            return ex


@onDispatch(event="message_create")
@EventBetween(after_month=8, before_month=10, before_day=13)
@Chance(1)
async def spawn_bonus(bot: Bot, data: Message):
    with bot.db.sql.session() as session:
        try:
            boss = Gladiator_Boss.get(session, data)
        except NotAvailable:
            return
    await boss.bonus(bot, data)


@register(group=Groups.ADMIN, main=manage, private_response=True)
async def spawn(ctx: Context, type: str, duration: timedelta, name: str = None) -> str:
    """
    Spawns Fighter or Bonus
    Params
    ------
    type:
        type to spawn
        Choices:
            Fighter = 0
            Bonus = 1
    duration:
        For how long message should stay active
    name:
        Boss to spawn for attacks
    """
    session = ctx.db.sql.session()
    boss = Gladiator_Boss.get(session, ctx, name)
    if int(type):
        _spawn = boss.bonus
    else:
        _spawn = boss.spawn

    if await _spawn(ctx.bot, ctx.data, _wait=duration.total_seconds()):
        return "Spawned successfully"
    return "No active boss to spawn"
