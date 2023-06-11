# MBot.py
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Open in Visual Studio Code](https://img.shields.io/static/v1?logo=visualstudiocode&label=&message=Open%20in%20Visual%20Studio%20Code&labelColor=2c2c32&color=007acc&logoColor=007acc)](https://open.vscode.dev/Mmesek/MBot.py)

[![CodeFactor Grade](https://img.shields.io/codefactor/grade/github/Mmesek/MBot.py)](https://www.codefactor.io/repository/github/mmesek/mbot.py)
[![Lines of code](https://sloc.xyz/github/Mmesek/MBot.py)]()
[![GitHub code size in bytes](https://img.shields.io/github/languages/code-size/Mmesek/MBot.py)]()
[![GitHub repo size](https://img.shields.io/github/repo-size/Mmesek/MBot.py)]()

[![GitHub issues](https://img.shields.io/github/issues/Mmesek/MBot.py)](../../issues)
[![GitHub pull requests](https://img.shields.io/github/issues-pr/Mmesek/MBot.py)](../../pulls)
[![GitHub contributors](https://img.shields.io/github/contributors/Mmesek/MBot.py)](../../graphs/contributors)

Bot commands/systems used by my personal M_Bot as well as Modmail on [Dying Light](https://discord.gg/dyinglight)'s server.

## Features
- [Modmail](bot/systems/modmail.py)
- [Logging](bot/dispatch/logging.py)
- [Stream](bot/dispatch/dispatch.py) Log (based on presence)
- [Infractions](bot/commands_slash/infractions.py)
- [Info](bot/commands_slash/info.py) (about Discord objects (User, Role, Channel, Guild etc)
- Basic [interacting](bot/commands_slash/mod.py) as bot - (Say/React)
- [Leaderboards](bot/commands_slash/leaderboards.py)
- [Giveaways](bot/commands_slash/giveaways.py)
- [Reaction](bot/dispatch/reactions.py)/[Presence](bot/dispatch/dispatch.py) [Roles](bot/systems/roles.py)
- Auto [Moderation](bot/dispatch/actions.py)
- [Ghostping](bot/dispatch/actions.py) detection
- Spoiler *[only](bot/dispatch/actions.py)* channel
- [Antiraid](bot/dispatch/guild.py) system (autokick)
- Database "[Stash](bot/commands_slash/database.py)" for memes/rules etc
- [Custom role](bot/commands_slash/database.py) for Nitro Users
- Tracking [Chat](bot/dispatch/actions.py)/[Voice](bot/dispatch/voice.py)/[Presence](bot/dispatch/dispatch.py) activity
- [Steam](bot/commands_slash/steam.py) calculator
- [Graphing](bot/commands_slash/graphs.py) (things like member join over time histograph)
- Auto dice roll in [RPG](bot/dispatch/actions.py) channels
- [Dynamic](bot/dispatch/dynamic.py) Voice Channel generation
- Miscellaneous commands for [random](bot/commands_slash/rand.py) rolls (Dice roll, coinflip etc)
- Various [converters](bot/commands_slash/converters.py) (Like Morse Transaltor, Making text upsidedown or Currency Converter)
- [Search](bot/commands_slash/search.py)ing other APIs (Like Steam, UrbanDict or Word Definitions)
- [Story](bot/commands_slash/story.py) conversation executor (Reads json or yaml file with story flow and responds to user accordingly)

## Minigames
- [Hangman](bot/commands_slash/games.py) game
- [Wordle](bot/commands_slash/games.py)
- [Halloween](bot/events/Halloween)
- Reaction [Hunt](bot/events/hunts.py) events
- [Christmas](bot/events/Christmas)

---

## Running locally

Run once to generate secrets.ini, modify to suit your needs.
Make sure to set `intents` in `bot` section to at least `1`.

#### Docker Compose:
```sh
docker-compose up
```

#### Docker
```sh
docker run -it Mmesek/MFramework \
    -v data:/app/data \
    -v bot:/app/bot \
    -v locale:/app/locale \
```

### Manually

#### Install required packages
```sh
python -m pip install -r requirements.txt
```

#### Run
```sh
python -m MFramework bot
```


# Contributing

1. Install dev dependencies
```sh
python -m pip install pre-commit black
```
2. Activate pre-commit
```sh
pre-commit install
```
3. Fork this repository
4. Make changes
5. Open Pull Request


### Contributing Guidelines:
- Keep your PR feature-specific
- Use numpydoc style for documentation
- If your command sends result like a message, Prefer to return it instead of calling send function
- Keep your commit messages descriptive, concise, under 50 characters and in imperative mood
- Sign your commits
