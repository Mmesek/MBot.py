from datetime import timedelta
from MFramework import Groups, Context, register#, Button, Snowflake
from typing import Dict

#buttons: Dict[str, Button] = {}
#messages: Dict[Snowflake, buttons] = {}

#class buttons(dict):
#    pass

#class Button(Button):
#    def __init__(self):
#        b = messages.get(self.message_id, buttons())
#        b[self.custom_id] = self
#        messages[self.message_id] = b

from MFramework.commands.components import Button, Interaction

class Poll(Button):
    def __init__(self, option, label, emoji=None):
        self.custom_id = f"poll_{option}"
        self.label = label
        self.emoji = emoji
        super().__init__()
    def __call__(ctx: Context, interaction: Interaction):
        return super().__call__(ctx, interaction)


@register(group=Groups.GLOBAL)
async def poll(ctx: Context, question: str, duration: timedelta = None, answer: str = None, answer_2: str = None, answer_3: str = None, answer_4: str = None, answer_5: str = None, *, language):
    '''
    Creates a poll
    Params
    ------
    question:
        Poll's Question
    duration:
        Poll's duration
    answer_*:
        Answer Option
    '''
    answers = [answer, answer_2, answer_3, answer_3, answer_4, answer_5]
    #answers = []
    answers = [Poll(option=x, label=answer) for x, answer in enumerate(answers)]
    await ctx.reply(question, components=answers)

    