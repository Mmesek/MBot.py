import enum

from mlib.types import Enum

from bot.database.db_types import *


class Statistic(Enum):
    Chat = 0
    Voice = 1
    Game = 2
    Spotify = 3
    Infractions_Active = 4
    Infractions_Total = 5

    DM_Total = 10
    DM_Forwarded = 11
    Spawned_Eggs = 12
    Spawned_Presents = 13
    Spawned_Pumpkins = 14
    # Spawned_Treats = 15
    # Spawned_Fear = 16
    # Spawned_Snowballs = 17
    Spawned_Moka = 18
    Spawned_GoldMoka = 19

    Halloween_Turn_Count = 20

    Story_Start = 30
    Story_End = 31


class Item(Enum):
    SYSTEM = 0  # Metadata Items
    Entity = 0  # Mobs
    Race = 0  # Race

    Event = 1  # Event Items

    Currency = 2  # Valuable on it's own
    Energy = 2  # Non static values like electric current or mana
    Fluid = 2  # Water

    Resource = 3  # Rocks
    Gift = 4  # Presents, items obtainable only via receiving from someone

    Weapon = 5  # Offensive
    Protection = 6  # Defensive

    Tool = 7  # Important utilities, like keys
    Potion = 8  # Consumable with effects
    Recipe = 9  # Crafting recipes
    Spell = 9  # Spells
    Book = 10  # Lore bits?

    Knowledge = 11  # Known "things" like recipes/spells

    Effects = 11  # Active effects
    # Booster = 11 # Active effects
    # Upgrade = 12 # Grants bonus stats to an item (Same as mod below tbh)
    Modification = 12  # Effects on item

    Experience = 13  # Experience in certain fields/skills?
    Reputation = 13  # Repuation received from other players (should be stat tbh), Standing with factions?

    Achievement = 14  # Collectible "Static" Achievements for certain actions
    Collectible = 14  # Hidden collectibles. Unlike above, they can be more "fluid"

    Utility = 15  # Usable item
    Miscellaneous = 16  # Fluff?
    Secret = 17  # Even I don't know
    Other = 18  # Catch-all


class Rarity(Enum):
    Trash = 0
    Event = 1
    Common = 2
    Uncommon = 3
    Rare = 4
    Epic = 5
    Legendary = 6
    Mythic = 7
    Exotic = 8
    Mystic = 9
    Special = 10
    Artifact = 11
    Relic = 12
    Cursed = 13
    Dark = 14


class Difficulty(Enum):
    Simple = 0
    Rookie = 1
    Novice = 2
    Easy = 3
    Normal = 4
    Hard = 5
    Deadly = 6
    Overkill = 7
    Nightmare = 8
    Hardcore = 9


class Reward(Enum):
    ITEM = Rarity.Common
    JUNK = Rarity.Common
    TWIG = Rarity.Common
    KEY = Rarity.Epic


class Present(Enum):
    WHITE = Rarity.Common
    TWIG = Rarity.Common
    GREEN = Rarity.Uncommon
    BLUE = Rarity.Rare
    RED = Rarity.Epic
    SOCK = Rarity.Event
    DARK = Rarity.Mythic
    CURSED = Rarity.Cursed
    GOLD = Rarity.Legendary


class ItemFlags(enum.IntFlag):
    Exclusive = 1 << 0
    Stackable = 1 << 1
    Tradeable = 1 << 2
    Purchasable = 1 << 3
    Special = 1 << 4
    Event = 1 << 5
    Drinkable = 1 << 6
    Edible = 1 << 7
    Giftable = 1 << 8


class HalloweenRaces(Enum):
    Human: Item.Race = "Human"  # , Item.Race ##818181
    Vampire: Item.Race = "Vampire"  # , Item.Race #6b1010 #a71919 #8f2727 #942710
    Werewolf: Item.Race = "Werewolf"  # , Item.Race #aa6b00
    Zombie: Item.Race = "Zombie"  # , Item.Race #03803c
    Hunter: Item.Race = "Hunter"  # , Item.Race #ad4949
    Huntsmen: Item.Race = "Huntsmen"  # , Item.Race #be923d
    Enchanter: Item.Race = "Enchanter"  # , Item.Race #4abe5f


class Flags(enum.IntFlag):
    Chat = 1 << 0
    Voice = 1 << 1
    Presence = 1 << 2
    Activity = 1 << 3
    Nitro = 1 << 4
