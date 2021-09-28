from MFramework import Groups, Context, register, Message, Embed, log, Snowflake
from typing import List, Dict, Union, Any
# Chapters can point to any other chapter, in any order _however_ if they do not point to any, next chapter in list should be used
# Subscribe to message changes, perhaps involve redis and pub/sub? 
# Otherwise "watch" message for updates
# Not all Story types will make use of updates but it still might be worth adding...
# Otherwise a type-related code is needed
# type being a variable object with duck typed methods?
# next should be some sort of iterator that switches currently active chapter
# Also better initializer could be pretty useful

try:
    import yaml
    def load_story(name, language='en') -> 'Story':
        with open(f'data/stories/{language}/{name}.yaml','r',newline='',encoding='utf-8') as file:
            story = yaml.safe_load(file)
        return Story(**story)
except ImportError:
    import json
    log.warn("Couldn't import yaml. Falling back to JSON as a stories format")
    def load_story(name, language="en") -> 'Story':
        with open(f'data/stories/{language}/{name}.json','r',newline='',encoding='utf-8') as file:
            story = json.load(file)
        return Story(**story)

class Base:
    name: str = "Error"
    description: Union[str, List[str]] = "Chapter not found"
    input_constraints: Dict[str, Any] = {}
    type: str
    reward: Dict[str, int]
    def __init__(self, **kwargs) -> None:
        for keyword, arg in kwargs.items():
            t = self.__annotations__.get(keyword)
            if type(arg) is list:
                updated = []
                for x, item in enumerate(arg):
                    if type(item) is dict and 'embed' in item:
                        item = Embed(**item['embed'])
                    updated.append(item)
                arg = updated
            if hasattr(t, '_name'):
                if t._name == 'Dict':
                    k, v  = t.__args__
                    if v not in {dict, list, str, int} and not hasattr(v, '_name') and type(arg) is dict and v is not type(arg):
                        #print(type(v), v)
                        #print(type(arg), arg)
                        #print(k)
                        arg = {_k: v(**_a) for _k, _a in arg.items()}
            setattr(self, keyword, arg)

    async def send_delayed_message(self, ctx: Context, message: str):
        import asyncio
        if type(message) is not Embed:
            await ctx.send(message)
            sleep = len(message)/60
        else:
            await ctx.send(embeds=[message])
            sleep = 10
        await ctx.deferred()
        await asyncio.sleep(sleep)

    async def send(self, ctx: Context, messages: List[str] = None) -> None:
        parts = messages or (self.description if type(self.description) is list else [self.description])
        for part in parts:
            await self.send_delayed_message(ctx, part)
    

class Chapter(Base):
    key: str
    choices: List[str]
    next: Dict[str, str]

    def get_next(self, answer: str) -> str:
        if len(self.next) > 1:
            return self.next.get(answer)
        return list(self.next.values())[0]

class Story(Base):
    chapters: Dict[str, Chapter] = {"start": Chapter()}
    choices: Dict[str, List[str]] = {} # Random.choice lists
    blacklisted_answers: List[str] = []
    intro: List[str] = []
    epilogue: List[str] = []
    errors: Dict[str, str] = {}
    webhook_id: Snowflake
    webhook_token: str

    async def check_constraints(self, input_constraints: Dict[str, Any], answer: Message) -> bool:
        constraints = {
            "only_digit": answer.content.isdigit(),
            "max_number": answer.content.isdigit() and int(answer.content) < 99999999,
            "min_length": len(answer.content),
            "min_words": len(set(answer.content.split(' ')))
        }
        for constraint, value in input_constraints.items():
            c = constraints.get(constraint, False)
            if type(c) is int and c < value:
                await answer.reply(self.errors.get(f"{constraint}_constraint", "Error"))
                return True
            elif type(value) is bool and value != c:
                await answer.reply(self.errors.get(f"{constraint}_constraint", "Wrong answer"))
                return True
            elif answer.content.lower() in self.blacklisted_answers:
                await answer.reply(self.errors.get("blacklisted_answer_constraint", "Wrong answer"))
                return True
        return False

    def next_chapter(self, chapter: Chapter, answer: str) -> Chapter:
        try:
            next = chapter.get_next(answer)
        except:
            next = list(self.chapters.keys())[list(self.chapters.keys()).index(chapter.key) + 1]
        return self.chapters.get(next, chapter)

class ContextStory:
    ctx: Context
    story: Story
    current_chapter: Chapter
    messages: Dict[Snowflake, Message]
    user_responses: Dict[str, Snowflake]
    def __init__(self, ctx: Context, story_name: str, language: str) -> None:
        self.ctx = ctx
        self.story = load_story(story_name, language)
        self.translated = {}
        for key, value in self.story.chapters.items():
            value.key = key
            self.story.chapters[key] = value
            self.translated[key] = value.name
        self.current_chapter = self.story.chapters.get("start", self.story.chapters.get(self.story.start))
        self.messages = {}
        self.user_responses = {}

    async def get(self, event: str="create", timeout: float=3600) -> Message:
        return await self.ctx.bot.wait_for(
                    "message_"+event if not self.ctx.is_dm else "direct_message_"+event, 
                    check=lambda x: x.author.id == self.ctx.user_id and 
                                    x.channel_id == self.ctx.channel_id and
                                    (x.content in self.current_chapter.choices 
                                    if getattr(self.current_chapter, 'choices', False) else True),
                    timeout=timeout)
    
    def watch(self, msg: Message):
        import asyncio
        async def update(msg):
            r = await self.ctx.bot.wait_for(
                "message_update" if not self.ctx.is_dm else "direct_message_update", 
                check=lambda x:
                    x.id == msg.id and
                    x.channel_id == msg.channel_id
            )
            self.messages[msg.id] = r

        asyncio.create_task(update(msg))

    async def chapter(self, *, skip_description: bool = False, event: str="create") -> None:
        if not skip_description:
            await self.current_chapter.send(self.ctx)

        m = await self.get(event)

        if await self.story.check_constraints(self.current_chapter.input_constraints, m):
            return await self.chapter(skip_description=True, event="update")

        self.save_response(m)
        try:
            self.next(m)
        except:
            return

        return await self.chapter()

    def next(self, msg: Message):
        self.current_chapter = self.story.next_chapter(self.current_chapter, msg.content)
    
    def save_response(self, message: Message) -> None:
        self.user_responses[self.current_chapter.key] = message.id
        self.messages[message.id] = message
    async def start(self):
        await self.story.send(self.ctx, self.story.intro)
        await self.chapter()
        await self.story.send(self.ctx, self.story.epilogue)
        from mlib.types import aInvalid
        answers = {k: self.messages.get(v).content for k, v in self.user_responses.items()}
        await types.get(self.story.type, aInvalid)(self.ctx, answers, self.translated, self.story.webhook_id, self.story.webhook_token)


@register(group=Groups.DM)
async def story(ctx: Context, name: str="createcharacter", *, language):
    '''Story Executor'''
    language='pl'
    story = ContextStory(ctx, name, language)
    await story.start()

async def createcharacter(ctx: Context, answers: Dict[str, str], translated: Dict[str, str]=None, wid: Snowflake=None, wtoken: str=None):
    from MFramework.database import alchemy as db
    s = ctx.db.sql.session()
    character = db.Character.filter(s, user_id=ctx.user_id).first()
    merge = False
    if character:
        merge = True
        #return
    else:
        character = db.Character(user_id=ctx.user_id)
    e = Embed()
    for answer in answers:
        if answer == 'items':
            items = answers[answer]
            from mlib.utils import upperfirst
            if ',' in items:
                delimiter = ","
            elif '\n- ' in items:
                delimiter = "- "
            else:
                delimiter = "\n"
            _items = [upperfirst(i.strip()) for i in items.split(delimiter) if i]
            from collections import Counter
            deduplicated_items = Counter(_items)
            deduplicated_items_values = list(deduplicated_items.values())
            deduplicated_items = list(deduplicated_items.keys())
            _items = [f"- ||{i}||" + f' x {deduplicated_items_values[x]}' if deduplicated_items_values[x] > 1 else f"- ||{i}||" for x, i in enumerate(deduplicated_items[:3])]
            items_ = '\n'.join(_items)
            e.addField("Posiadane Przedmioty", items_, inline=True)
        else:
            if answer == 'color':
                color = answers[answer]
                try:
                    if "#" in color:
                        color = int(color.replace("#", ""), 16)
                    else:
                        rgb = [int(i) for i in color.replace(" ","").split(",")]
                        from mlib.colors import getIfromRGB
                        color = getIfromRGB(rgb)
                except Exception as ex:
                    color = 0
                answers[answer] = color
            if answer not in {"name", "color", "story"}:
                e.addField(translated.get(answer), f"||{answers[answer]}||", inline=True)
            if answer == 'gender':
                answers[answer] = True if 'Mężczyzna' in answers[answer] else False
            setattr(character, answer, answers[answer])
    if merge:
        s.merge(character)
    else:
        s.add(character)
    s.commit()
    e.setTitle(character.name).setColor(character.color).setDescription(character.story)
    await ctx.reply(embeds=[e])
    await ctx.bot.execute_webhook(webhook_id=wid, webhook_token=wtoken, username=ctx.user.username, embeds=[e])

async def survey(ctx: Context, answers: Dict[str, str], translated: Dict[str, str]=None, wid: Snowflake=None, wtoken: str=None):
    e = Embed()
    for answer in answers:
        e.addField(translated.get(answer), answers[answer])
    await ctx.reply(embeds=[e])
    e.setAuthor(f"{ctx.user.username}#{ctx.user.discriminator}", icon_url=ctx.user.get_avatar()).setFooter(ctx.user_id)
    await ctx.bot.execute_webhook(wid, wtoken, embeds=[e])

@register(group=Groups.DM, interaction=False)
async def modapp(ctx: Context):
    '''
    Apply for a mod!
    '''
    return await story(ctx, "modapp", language="en")

types = {
    "createcharacter":createcharacter,
    "survey":survey
}


#@register(group=Groups.MODERATOR)
async def conversation(bot: 'HTTP_Client', filename: str, *, channel_id: Snowflake, default_username: str, webhook_id: Snowflake, webhook_token: str):
    '''Runs linear conversation flow'''
    with open(f'data/{filename}.md','r',newline='',encoding='utf-8') as file:
        lines = file
    for line in lines:
        slept = False
        if line.startswith('#') or line.strip() == '' or line.startswith('//'):
            continue
        if ":" in line:
            username, content = line.split(':', 1)
        else:
            username = default_username
            content = line
            if 'później' in line:
                from mlib.converters import total_seconds
                sleep = total_seconds(line).seconds
                slept = True
            await bot.trigger_typing_indicator(channel_id)
            await asyncio.sleep(sleep)
        if '#' in content and '%' in content:
            l = content.split('#',1)
            content = l[0]
            sleep /= int(l[1].strip().split('%',1)[0].strip()) / 100
        if '//' in content:
            content = content.split('//',1)[0]
        sleep = len(content.split(' ')) * 0.73
        await bot.execute_webhook(webhook_id, webhook_token, username=username, content=content)
        if not slept:
            await bot.trigger_typing_indicator(channel_id)
            await asyncio.sleep(sleep)
    


if __name__ == "__main__":
    from mlib import arguments
    from mdiscord.http_client import HTTP_Client
    arguments.add("--token", help="Specifies bot token to use")
    arguments.add("--user", help="Specifies user id to use")
    arguments.add("--webhook", help="Specifies webhook id to use")
    arguments.add("--webhook_token", help="Specifies webhook token to use")
    arguments.add("--username", help="Specifies default username to use")
    arguments.add("--avatar", help="Specifies default avatar to use")
    arguments.add("--channel", help="Specifies channel that should receive messages")
    arguments.add("--filename", help="Specifies conversation file to play")
    import asyncio
    async def main():
        args = arguments.parse()
        e = HTTP_Client(args.token, args.user_id)
        await conversation(e, args.filename, default_username=args.username, webhook_id=args.webhook_id, webhook_token=args.webhook_token)
    asyncio.run(main())
