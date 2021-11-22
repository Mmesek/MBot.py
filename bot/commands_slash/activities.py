from enum import Enum

from MFramework import register, Groups, Context, Channel, Invite_Target_Types

class Activities(Enum):
    Watch_Together = 880218394199220334
    Poker_Night = 755827207812677713
    Betrayal = 773336526917861400
    Fishington = 814288819477020702
    Chess = 832012774040141894
    Checkers = 832013003968348200
    Sketchy_Artist = 879864070101172255
    Awkword = 879863881349087252
    Putts = 832012854282158180
    Doodle_Crew = 878067389634314250
    Letter_Tile = 879863686565621790
    World_Snacks = 879863976006127627
    SpellCast = 852509694341283871


@register(group=Groups.NITRO)
async def activity(ctx: Context, channel: Channel, activity: Activities) -> str:
    '''
    Start activity in selected voice channel
    Params
    ------
    channel: Voice
        voice channel to start activity in
    activity:
        activity to start (Not all them might work)
    '''
    invite = await ctx.bot.create_channel_invite(channel.id, target_type=Invite_Target_Types.EMBEDDED_APPLICATION, target_application_id=activity.value)
    return f"[Click here to join {invite.target_application.name} in {invite.channel.name}!](<https://discord.gg/{invite.code}>)"