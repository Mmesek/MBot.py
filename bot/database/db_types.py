from MFramework import Groups
from mlib.types import Enum

from bot.utils.permissions import Permissions


class Snippet(Permissions):
    """Snippets"""

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
    DM_Reply: Groups.MODERATOR = (22, "Thanks for contacting mod team!")
    Forum_Autoreply: Groups.MODERATOR = (23, "Hey, thanks for creating a post!")


class Task(Enum):
    Generic = 0
    Giveaway = 1
    Hidden_Giveaway = 2
    Reminder = 3
    Quest = 4
