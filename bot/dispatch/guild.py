from MFramework import Bot, Guild_Member_Add, Guild_Member_Remove, log, onDispatch


@onDispatch
async def guild_member_add(self: Bot, data: Guild_Member_Add):
    await self.db.influx.influxMember(data.guild_id, data.user.id, True, data.joined_at)


@onDispatch
async def guild_member_remove(self: Bot, data: Guild_Member_Remove):
    await self.db.influx.influxMember(data.guild_id, data.user.id, False)


@onDispatch(event="guild_member_add")
async def initial_welcome_message(self: Bot, data: Guild_Member_Add):
    if data.guild_id not in {289739584546275339, 968770411527557120}:
        return
    welcome_message = """
Hey! Welcome to *the official Dying Light Discord server*! I'm a **community**-made bot that forwards **ANY** message you send to me directly to the __Server Moderation__ Team!

Feel free to message me whenever you have an issue, suggestion or really anything related to the Discord **server**.
Please, do not DM moderation directly for these matters.

However, If you need to reach Techland, you can either directly contact the Community Manager, <@210060521238560768>, send them an email to `support@techland.pl` or use their website: https://support.techland.pl/

Some links:

<https://store.techland.net/> - Techland Store
<https://techland-merch.com/> - Techland Merch
<https://techlandgg.com/> - Get in game rewards and complete challenges

Under any circumstances, do **not** DM or @ping ANY other Techland employee other than <@210060521238560768> on the server.

__***THIS IS AN AUTOMATED MESSAGE. DO NOT REPLY, AS YOUR MESSAGES WILL BE SENT TO THE SERVER MODERATION.***__
"""
    welcome_message_fr = """
Bienvenue sur le serveur Discord officiel Dying Light FR! Je suis un robot créé par la **communauté** qui transmet TOUS les messages que vous m'envoyez directement à l'équipe de __modération du serveur__ !

N'hésitez pas à m'envoyer un message si vous avez un problème, une suggestion ou tout ce qui concerne le serveur Discord.
S'il vous plaît, n'envoyez MP à la modération directement pour ces questions.

Cependant, si vous avez besoin de joindre Techland, vous pouvez communiquer directement avec le Community Manager, <@210060521238560768>, leur envoyer un email à `support@techland.pl` ou utiliser leur site web: https://support.techland.pl/.

Quelques liens :

<https://store.techland.net/> - Techland Store
<https://techland-merch.com/> - Techland Merch
<https://techlandgg.com/> - Obtenez des récompenses en jeu et relevez des défis.

En toutes circonstances, n'envoyez MP ou @ping à un employé de Techland autre que @Uncy sur le serveur.


__***CECI EST UN MESSAGE AUTOMATISÉ. NE RÉPONDEZ PAS, CAR VOS MESSAGES SERONT ENVOYÉS À LA MODÉRATION DU SERVEUR.***__
"""
    try:
        channel = await self.create_dm(data.user.id)
        await self.create_message(
            channel.id, welcome_message if data.guild_id == 289739584546275339 else welcome_message_fr
        )
    except:
        log.debug("Couldn't DM welcome message to %s. Possibly due to user blocking DMs from non-friends")
