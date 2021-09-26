import enum

from mlib.types import Enum
from MFramework.database.alchemy.types import *

class Infraction(Permissions):
    '''Infractions'''
    Warn: Groups.HELPER = (0, "Warns user")
    Mute: Groups.MODERATOR = (1, "Mutes user")
    Kick: Groups.MODERATOR = (2, "Kicks user")
    Ban: Groups.MODERATOR = (3, "Bans user")
    Temp_Mute: Groups.HELPER = (4, "Temporarly mutes user")
    Temp_Ban: Groups.HELPER = (5, "Temporarly bans user")
    Unban: Groups.ADMIN = (6, "Unbans user")
    Unmute: Groups.MODERATOR = (7, "Unmutes user")
    Limbo: Groups.ADMIN = (8, "Throws user to Limbo")
    DM_Mute: Groups.MODERATOR = (9, "Mutes DMs from user in Modmail")
    DM_Unmute: Groups.MODERATOR = (10, "Unmutes DMs from user in Modmail")
    Report: Groups.GLOBAL = (11, "Reports user")


class Snippet(Permissions):
    '''Snippets'''
    Snippet: Groups.MODERATOR = (0, "Snippet text")
    Regex: Groups.MODERATOR = (1, "Regular Expression")
    Rule: Groups.MODERATOR = (2, "!r")
    Emoji: Groups.HELPER = (3, ":emoji:")
    Reaction: Groups.MODERATOR = (4, "Reaction to a message")
    Canned_Response: Groups.MODERATOR = (5, "DM: Hi. - Hello")
    Meme: Groups.NITRO = (6, "That's funny")
    Quote: Groups.NITRO = (7, "Someone said...")
    Question: Groups.MODERATOR = (8, "What would you say?")
    Answer: Groups.MODERATOR = (9, "Cool story bro")
    Blacklisted_Word: Groups.MODERATOR = (17, "f$@#!")
    Whitelisted: Groups.MODERATOR = (18, "https://google.com/")
    Response_Reaction: Groups.MODERATOR = (19, "Works: ✔")
    Stream: Groups.MODERATOR = (20, "Someone is Streaming... HEY CHECK THEM OUT!")
    Definition: Groups.NITRO = (21, "Admin - Person you don't want to mess with")


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

    Halloween_Turn_Count = 20


class Item(Enum):
    SYSTEM = 0 # Metadata Items
    Entity = 0 # Mobs
    Race = 0 # Race

    Event = 1 # Event Items

    Currency = 2 # Valuable on it's own
    Energy = 2 # Non static values like electric current or mana
    Fluid = 2 # Water
    
    Resource = 3 # Rocks
    Gift = 4 # Presents, items obtainable only via receiving from someone 
    
    Weapon = 5 # Offensive
    Protection = 6 # Defensive
    
    Tool = 7 # Important utilities, like keys
    Potion = 8 # Consumable with effects
    Recipe = 9 # Crafting recipes
    Spell = 9 # Spells
    Book = 10 # Lore bits?
    
    Knowledge = 11 # Known "things" like recipes/spells
    
    Effects = 11 # Active effects
    #Booster = 11 # Active effects
    #Upgrade = 12 # Grants bonus stats to an item (Same as mod below tbh)
    Modification = 12 # Effects on item 

    Experience = 13 # Experience in certain fields/skills?
    Reputation = 13 # Repuation received from other players (should be stat tbh), Standing with factions?

    Achievement = 14 # Collectible "Static" Achievements for certain actions
    Collectible = 14 # Hidden collectibles. Unlike above, they can be more "fluid"

    Utility = 15 # Usable item
    Miscellaneous = 16 # Fluff?
    Secret = 17 # Even I don't know
    Other = 18 # Catch-all


class Task(Enum):
    Generic = 0
    Giveaway = 1
    Hidden_Giveaway = 2
    Reminder = 3
    Quest = 4


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
    Human = 0, Item.Race
    Vampire = 1, Item.Race
    Werewolf = 2, Item.Race
    Zombie = 3, Item.Race
    Hunter = 4, Item.Race
    Huntsmen = 5, Item.Race
    Enchanter = 6, Item.Race
