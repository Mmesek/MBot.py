from MFramework import Context, Groups, Role, register
from MFramework.database.alchemy import Role as db_Role
from MFramework.database.alchemy import types

from . import role


@register(group=Groups.ADMIN, main=role)
async def level():
    """Management of Level roles"""
    pass


@register(group=Groups.ADMIN, main=level, private_response=True)
async def create(ctx: Context, role: Role, exp: int = 0) -> str:
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
    session = ctx.db.sql.session()
    r = db_Role.fetch_or_add(session, server_id=ctx.guild_id, id=role.id)
    r.add_setting(types.Setting.Level, exp)
    session.commit()

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
async def remove(ctx: Context, role: Role) -> str:
    """
    Removes level role
    Params
    ------
    role:
        role to remove
    """
    session = ctx.db.sql.session()
    r = session.query(db_Role).filter(db_Role.server_id == ctx.guild_id, db_Role.id == role.id).first()
    if r:
        ctx.cache.level_roles.remove((r.id, r.get_setting(types.Setting.Level)))
        ctx.cache.level_roles.sort(key=lambda x: x[1])
        r.remove_setting(types.Setting.Level)
        session.commit()
        return f"Level {role.name} removed successfully"

    return f"Level role {role.name} doesn't exist!"
