# MBot.py
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Open in Visual Studio Code](https://open.vscode.dev/badges/open-in-vscode.svg)](https://open.vscode.dev/Mmesek/MBot.py)

Bot commands/systems used by my personal M_Bot as well as Modmail on [Dying Light](https://discord.gg/dyinglight)'s server.

Features:
- [Modmail](bot/systems/modmail.py)
- [Logging](bot/dispatch/logging.py)
- [Stream](bot/dispatch/dispatch.py) Log (based on presence)
- [Infractions](bot/slash/infractions.py)
- [Info](bot/slash/info.py) (about Discord objects (User, Role, Channel, Guild etc)
- Basic [interacting](bot/slash/mod.py) as bot - (Say/React)
- [Leaderboards](bot/slash/leaderboards.py)
- [Giveaways](bot/slash/giveaways.py)
- [Reaction](bot/dispatch/reactions.py)/[Presence](bot/dispatch/dispatch.py) [Roles](bot/systems/roles.py)
- Auto [Moderation](bot/dispatch/actions.py)
- [Ghostping](bot/dispatch/actions.py) detection
- Spoiler *[only](bot/dispatch/actions.py)* channel
- [Antiraid](bot/dispatch/guild.py) system (autokick)
- Database "[Stash](bot/slash/database.py)" for memes/rules etc
- [Custom role](bot/slash/database.py) for Nitro Users
- Tracking [Chat](bot/dispatch/actions.py)/[Voice](bot/dispatch/voice.py)/[Presence](bot/dispatch/dispatch.py) activity
- [Steam](bot/slash/steam.py) calculator
- [Graphing](bot/slash/graphs.py) (things like member join over time histograph)
- Auto dice roll in [RPG](bot/dispatch/actions.py) channels
- [Dynamic](bot/dispatch/dynamic.py) Voice Channel generation
- Miscellaneous commands for [random](bot/slash/rand.py) rolls (Dice roll, coinflip etc)
- Various [converters](bot/slash/converters.py) (Like Morse Transaltor, Making text upsidedown or Currency Converter)
- [Search](bot/slash/search.py)ing other APIs (Like Steam, UrbanDict or Word Definitions)
- [Story](bot/slash/story.py) conversation executor (Reads json or yaml file with story flow and responds to user accordingly)

Minigames:
- [Hangman](bot/slash/rand.py) game
- [Wordle](bot/slash/rand.py)
- [Halloween](bot/events/Halloween)
- Reaction [Hunt](bot/events/hunts.py) events
- [Christmas](bot/events/Christmas)

Launch via docker-compose:
```sh
docker-compose up
```

Or manually via Docker:
```sh
docker run -it Mmesek/MFramework \
    -v data:/app/data \
    -v bot:/app/bot \
    -v repos:/repos
```

Set crontab:
```sh
crontab -e
@reboot sleep 40 && /bin/bash /home/pi/MBot.py/mbot.sh
```

Install required packages:
```sh
python3.7 pip install -r requirements.txt
```
