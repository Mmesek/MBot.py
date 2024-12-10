from MFramework import Groups, Role, register

from bot import Context
from bot import database as db
from bot.systems.roles import role


@register(group=Groups.ADMIN, main=role)
async def level():
    """Management of Level roles"""
    pass


@register(group=Groups.ADMIN, main=level, private_response=True)
async def create(ctx: Context, role: Role, exp: int = 0, *, session: db.Session) -> str:
    """Create/Update level role

    Params
    ------
    role:
        Role which should be awarded for reaching these values
    exp:
        Chat exp required to gain this role
    req_voice:
        Voice exp required to gain this role
    type:
        Whether both, either or in total exp should award this role
    """
    r = await db.Role.fetch_or_add(session, server_id=ctx.guild_id, id=role.id)
    r.exp_req = exp

    ctx.cache.level_roles.append((r.id, exp))
    ctx.cache.level_roles.sort(key=lambda x: x[1])

    return f"Level {role.name} added successfully"


@register(group=Groups.ADMIN, main=level, private_response=True)
async def list_(ctx: Context) -> str:
    """Shows list of current level roles"""
    return (
        "\n".join(f"{getattr(await ctx.cache.roles.get(i[0]), 'name', None)} - {i[1]}" for i in ctx.cache.level_roles)
        or "None set"
    )


@register(group=Groups.ADMIN, main=level, private_response=True)
async def remove(ctx: Context, role: Role, *, session: db.Session) -> str:
    """
    Removes level role
    Params
    ------
    role:
        role to remove
    """
    r = await db.Role.get(session, db.Role.server_id == ctx.guild_id, db.Role.id == role.id)
    if r:
        ctx.cache.level_roles.remove((r.id, r.exp_req))
        ctx.cache.level_roles.sort(key=lambda x: x[1])
        r.exp_req = None
        return f"Level {role.name} removed successfully"

    return f"Level role {role.name} doesn't exist!"
