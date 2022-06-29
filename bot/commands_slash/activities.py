from MFramework import Context, Groups, Invite_Target_Types, register


@register(group=Groups.GLOBAL)
async def activity(ctx: Context, activity: str) -> str:
    """
    Start activity in selected voice channel
    Params
    ------
    activity:
        activity to start (Not all them might work)
        Choices:
            Watch Together = 880218394199220334
            Poker Night = 755827207812677713
            Betrayal.io = 773336526917861400
            Fishington.io = 814288819477020702
            Chess = 832012774040141894
            Checkers = 832013003968348200
            Sketchy Artist = 879864070101172255
            Awkword (Cards against Humanity) = 879863881349087252
            Putts (Doesn't Work) = 832012854282158180
            Doodle Crew (Drawing) = 878067389634314250
            Letter Tile (Scrabble) = 879863686565621790
            Word Snacks = 879863976006127627
            SpellCast = 852509694341283871
            Decoders (Guess Card) = 891001866073296967
            Ocho = 832025144389533716
            Youtube Together = 755600276941176913
    pass:
        pass
    """
    channel_id = next(filter(lambda x: ctx.user_id in ctx.cache.voice.get(x, []), ctx.cache.voice), None)
    if not channel_id:
        return "You have to be in a voice channel first! Join some and then use the command again!"
    invite = await ctx.bot.create_channel_invite(
        channel_id, target_type=Invite_Target_Types.EMBEDDED_APPLICATION, target_application_id=activity
    )
    return f"[Click here to join {invite.target_application.name} in {invite.channel.name}!](<https://discord.gg/{invite.code}>)"
