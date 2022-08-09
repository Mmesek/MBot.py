from datetime import datetime, timedelta, timezone

import sqlalchemy as sa
import sqlalchemy.orm as orm
from MFramework import Context, Embed, Groups, register
from MFramework.utils.leaderboards import Leaderboard, Leaderboard_Entry
from mlib.database import Base


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
    user_id: int = sa.Column(sa.ForeignKey("Gladiator.id"))
    boss_id: int = sa.Column(sa.ForeignKey("Gladiator_Boss.id"))
    damage: int = sa.Column(sa.Integer, default=0)
    bonus: int = sa.Column(sa.Integer, default=0)
    timestamp: datetime = sa.Column(sa.TIMESTAMP(True), server_default=sa.func.now())


class Cooldown(Exception):
    pass


class Gladiator_Boss(Base):
    id: int = sa.Column(sa.Integer, primary_key=True)
    guild_id: int = sa.Column(sa.BigInteger)
    health: int = sa.Column(sa.Integer, nullable=False)
    name: str = sa.Column(sa.String, nullable=False)
    start_at: datetime = sa.Column(sa.TIMESTAMP(True), server_default=sa.func.now())
    ends_at: datetime = sa.Column(sa.TIMESTAMP(True), nullable=False)
    image_url: str = sa.Column(sa.String)

    def attack(self, session, user_id: int) -> int:
        player = (
            session.query(Gladiator).filter(Gladiator.user_id == user_id, Gladiator.guild_id == self.guild_id).first()
        )
        if not player:
            player = Gladiator(user_id=user_id, guild_id=self.guild_id)
            session.add(player)

        history = [i for i in player.history if i.damage]

        if history:
            remaining_cooldown = timedelta(minutes=30) - (datetime.now(tz=timezone.utc) - history[-1].timestamp)
        else:
            remaining_cooldown = timedelta()

        if remaining_cooldown.total_seconds() > 0:
            raise Cooldown(f"Cooldown remaining: {remaining_cooldown}")

        return player.add_attack(self)


@register(group=Groups.GLOBAL)
async def arena():
    pass


@register(group=Groups.ADMIN, main=arena)
async def create(ctx: Context, name: str, health: int, duration: timedelta, image: str = None):
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
        return "Boss already exists"

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


def get_boss(session, ctx: Context, name: str = None) -> Gladiator_Boss:
    boss = (
        session.query(Gladiator_Boss)
        .filter(Gladiator_Boss.ends_at >= ctx.data.id.as_date.astimezone(timezone.utc))
        .filter(Gladiator_Boss.guild_id == ctx.guild_id)
        .filter(Gladiator_Boss.health > 0)
    )

    if name:
        boss = boss.filter(Gladiator_Boss.name == name)

    boss = boss.first()

    if not boss:
        raise Exception("Couldn't find provided boss")
    return boss


@register(group=Groups.GLOBAL, main=arena)
async def check(ctx: Context, name: str = None):
    """
    Checks remaining boss's health
    Params
    ------
    name:
        Name of the boss to check
    """
    session = ctx.db.sql.session()

    boss = get_boss(session, ctx, name)

    return boss.health


@register(group=Groups.GLOBAL, main=arena)
async def attack(ctx: Context, name: str = None, user_id: int = None, *, session=None):
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

    boss = get_boss(session, ctx, name)
    if ctx.data.id.as_date.astimezone(timezone.utc) > boss.ends_at:
        return "Boss is not available anymore!"
    elif boss.health <= 0:
        return "Boss has already been slain!"

    dmg = boss.attack(session, user_id or ctx.user_id)
    session.commit()

    return f"Dealt {dmg} to {boss.name}"


@register(group=Groups.MODERATOR, main=arena)
async def bonus(ctx: Context, bonus: int, user_id: int = None, *, session=None):
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

    player.add_bonus(bonus)
    session.commit()

    return player.bonus(get_boss(session, ctx))


@register(group=Groups.GLOBAL, main=arena)
async def stats(ctx: Context, user_id: int = None, *, session=None):
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
    embed.add_field("Current damage bonus", str(player.bonus(get_boss(session, ctx))), True)
    if player.history:
        embed.add_field("Total damage dealt", str(sum([i.damage for i in player.history])), True)
        embed.add_field("Last attack", str(player.history[-1].timestamp) + " UTC", True)
        remaining_cooldown = timedelta(minutes=30) - (datetime.now(tz=timezone.utc) - player.history[-1].timestamp)
        if remaining_cooldown.total_seconds() > 0:
            embed.add_field("Cooldown remaining", str(remaining_cooldown), True)
    return embed


@register(group=Groups.GLOBAL, main=arena)
async def leaderboard(ctx: Context, *, session=None):
    """
    Shows leaderboards
    """
    return Leaderboard(ctx, ctx.user_id, [Leaderboard_Entry(ctx, i[0], i[1]) for i in await list_users(ctx)]).as_embed()


@register(group=Groups.GLOBAL, main=arena)
async def list_bosses(ctx: Context):
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
    bosses: list[Gladiator_Boss] = session.query(Gladiator_Boss).order_by(Gladiator_Boss.ends_at).all()
    return "\n".join([f"{boss.name} - {boss.health} | {boss.ends_at}" for boss in bosses])


async def list_users(ctx: Context, min_damage: int = 1, *, session=None):
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
