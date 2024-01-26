from MFramework import (
    Context,
    Groups,
    Interaction,
    Interaction_Application_Command_Callback_Data,
    Interaction_Callback_Type,
    Interaction_Response,
    Message,
    register,
)
from MFramework.commands.components import Button, Row, TextInput


def load_story(name, language="en") -> "Story":
    path = f"data/stories/{language}/{name}"
    try:
        import yaml

        with open(f"{path}.yaml", "r", newline="", encoding="utf-8") as file:
            story = yaml.safe_load(file)
    except (ImportError, FileNotFoundError):
        import json

        with open(f"{path}.json", "r", newline="", encoding="utf-8") as file:
            story = json.load(file)
    return Story(**story)


class ConstraintError(Exception):
    pass


class Constraint:
    blacklisted: list[str]
    only_digit: bool = False

    min_length: int = 0
    max_length: int = None

    min_words: int = 0
    max_words: int = None

    def check(self, input: str) -> None:
        if self.only_digit and not input.isdigit():
            raise ConstraintError("only_digit")
        elif self.blacklisted and input not in self.blacklisted:
            raise ConstraintError("blacklisted")

        elif not self.min_length < len(input):
            raise ConstraintError("min_lenght")
        elif self.max_length and not len(input) <= self.max_length:
            raise ConstraintError("max_lenght")

        elif not self.min_words < len(input.split(" ")):
            raise ConstraintError("min_words")
        elif self.max_words and not len(input.split(" ")) <= self.max_words:
            raise ConstraintError("max_words")


class Node:
    name: str
    key: str
    next_node: list[str]


class Input(Node):
    choices: list[str]
    constraints: Constraint
    errors: dict[str, str]

    async def send_prompt(self, ctx: Context, prompt: str):
        if self.choices:
            await self.send_buttons(ctx, prompt)
        elif (
            self.constraints.min_length
            or self.constraints.max_length
            or self.constraints.min_words
            or self.constraints.max_words
        ):
            await self.send_modal(ctx, prompt)
        else:
            await self.send_message(ctx, prompt)

    async def send_buttons(self, ctx: Context, prompt: str) -> str:
        await ctx.send(prompt, components=Row(Button(choice, f"choice-{self.key}") for choice in self.choices))
        answer = await self.get_interaction(ctx, f"Button-choice-{self.key}")
        await answer.reply("Ok", private=True)

        return answer.data.name

    async def send_modal(self, ctx: Context, prompt: str):
        await ctx.send(
            prompt,
            components=Row(Button("Click me", f"modal-request-{self.key}")),
        )
        r = await self.get_interaction(ctx, f"Button-modal-request-{self.key}")

        await ctx.bot.create_interaction_response(
            r.id,
            r.token,
            Interaction_Response(
                type=Interaction_Callback_Type.MODAL,
                data=Interaction_Application_Command_Callback_Data(
                    title=self.name,
                    custom_id=self.key,
                    components=Row(
                        TextInput(
                            prompt,
                            min_length=self.constraints.min_length or self.constraints.min_words * 5,
                            max_length=self.constraints.max_length or self.constraints.max_words * 5,
                        )
                    ),
                ),
            ),
        )
        answer = await self.get_interaction(ctx, f"Modal-{self.key}")
        await answer.reply("Ok", private=True)

        return answer.data.values

    async def send_message(self, ctx: Context, prompt: str):
        await ctx.send(prompt)
        msg = await self.get_message(ctx)
        return msg.content

    async def get_interaction(self, ctx: Context, custom_id: str) -> Interaction:
        return await ctx.bot.wait_for(
            "interaction_create",
            check=lambda x: x.data.custom_id == custom_id and (x.user or x.member.user).id == ctx.user_id,
            timeout=1800,
        )

    async def get_message(self, ctx: Context, event: str = "create", timeout: int = 3600) -> Message:
        return await ctx.bot.wait_for(
            "message_" + event if not ctx.is_dm else "direct_message_" + event,
            check=lambda x: x.author.id == ctx.user_id and x.channel_id == ctx.channel_id,
            timeout=timeout,
        )

    async def take_input(self, ctx: Context, prompt: str):
        answer = await self.send_prompt(ctx, prompt)

        try:
            self.constraints.check(answer)
        except ConstraintError as ex:
            error = self.errors.get(ex, self.errors.get(f"{self.key}_{ex}", self.errors.get("generic")))
            return await self.take_input(ctx, error)

        return answer


class Chapter(Input):
    description: str

    async def play(self, ctx: Context) -> tuple[str]:
        answer = await self.take_input(ctx, self.description)
        # NOTE: Any additional logic might go here, including selecting next_node
        return answer, self.next_node


class Story:
    chapters: dict[str, Chapter]
    current: str

    def __init__(self, chapters: dict[str, dict], start: str, **kwargs) -> None:
        for x, chapter in enumerate(chapters.values()):
            if not chapter.get("next", None) and x < len(chapters):
                chapter["next"] = chapters[x + 1]

        self.chapters = {name: Chapter(**chapter, key=name) for name, chapter in chapters.items()}
        self.current = start

    async def play(self, ctx: Context) -> dict[str, str]:
        answers = {}
        while self.current:
            answers[self.current], self.current = await self.chapters[self.current].play(ctx)
        return answers


@register(group=Groups.DM)
async def start(ctx: Context, story: str):
    """
    Story runner
    Params
    ------
    story:
        Story to run
    """
    _story = load_story(story, ctx.language)
    try:
        result = await _story.play(ctx)
    except TimeoutError:
        return "Waited too long for a response. Start again if you want to try again."
