from MFramework import Bot, Message_Reaction_Add, Message_Reaction_Remove, onDispatch


@onDispatch
async def message_reaction_add(self: Bot, data: Message_Reaction_Add):
    if data.guild_id == 0 or data.member and data.member.user.bot:
        return

    roles = self.cache[data.guild_id].reaction_roles
    if roles == {}:
        return
    r = None
    for group in roles:
        for msg in roles[group]:
            if data.message_id == msg:
                r = roles[group][data.message_id][f"{data.emoji.name}:{data.emoji.id or 0}"]
                if group is None:
                    continue
                elif all(i in data.member.roles for i in r):
                    return
                elif any(
                    i in data.member.roles for i in [j for e in roles[group][data.message_id].values() for j in e]
                ):
                    return await self.delete_user_reaction(
                        data.channel_id,
                        data.message_id,
                        f"{data.emoji.name}:{data.emoji.id}" if data.emoji.id else data.emoji.name,
                        data.user_id,
                    )
    if r == None:
        return
    for i in r:
        await self.add_guild_member_role(data.guild_id, data.user_id, i, "Reaction Role")


@onDispatch
async def message_reaction_remove(self: Bot, data: Message_Reaction_Remove):
    if data.guild_id == 0:
        return
    roles = self.cache[data.guild_id].reaction_roles
    if roles == {}:
        return
    role = None
    for group in roles:
        if data.message_id in roles[group]:
            role = roles[group][data.message_id][f"{data.emoji.name}:{data.emoji.id or 0}"]
            if role == None:
                return
            break
    if role == None:
        return
    for i in role:
        await self.remove_guild_member_role(data.guild_id, data.user_id, i, "Reaction Role")
