MBot.py
---

Bot commands/systems used by my personal M_Bot as well as Modmail on [Dying Light](https://discord.gg/dyinglight)'s server.

Features:
- [Modmail](bot/systems/modmail.py)
- [Logging](bot/dispatch/logging.py)
- [Infractions](bot/slash/infractions.py)
- [Info](bot/slash/info.py)
- [Leaderboards](bot/slash/leaderboards.py)
- [Giveaways](bot/slash/giveaways.py)
- [Reaction](bot/dispatch/reactions.py)/[Presence](bot/dispatch/dispatch.py) [Roles](bot/systems/roles.py)
- Auto [Moderation](bot/dispatch/actions.py)
- Database "[Stash](bot/slash/database.py)" for memes/rules etc
- [Custom role](bot/slash/database.py) for Nitro Users
- Tracking [Chat](bot/dispatch/actions.py)/[Voice](bot/dispatch/voice.py)/[Presence](bot/dispatch/dispatch.py) activity
- [Halloween](bot/events/Halloween) minigame
- [Steam](bot/slash/steam.py) calculator
- [Graphing](bot/slash/graphs.py)
- Auto dice roll in [RPG](bot/dispatch/actions.py) channels
- Miscellaneous commands for [random](bot/slash/rand.py) rolls
- Various [converters](bot/slash/converters.py)
- [Search](bot/slash/api.py)ing other APIs
- [Story](bot/slash/context.py) executor

Set crontab:
```sh
crontab -e
@reboot sleep 40 && /bin/bash /home/pi/MBot.py/mbot.sh
```

Install required packages:
```sh
python3.7 pip install -r requirements.txt
```