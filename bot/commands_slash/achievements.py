import re
from datetime import timedelta

import aiohttp
from MFramework import Context, Groups, register

CHAPTER_PATTERN = re.compile(
    r"(?:(?P<Minute>\d+):(?P<Second>\d+)) ?- ?(?P<Challenge>[^-\n]+)(?: ?- ?(?P<Checkpoint>\w+))?"
)


class Chapter:
    def __init__(self, minute: int, second: int, checkpoint: str) -> None:
        self.timestamp = timedelta(minutes=int(minute), seconds=int(second))
        self.checkpoint = checkpoint


@register(group=Groups.GLOBAL, guild=289739584546275339)
async def achievements(ctx: Context, achievement: str, url: str):
    """
    Submit a video for achievement!
    Params
    ------
    achievement:
        Achievement to submit
        Choices:
            True Night Runner = True Night Runner
    url:
        URL to a YT video with a proof
    """
    video_id = url.split("=")[-1]
    token = ctx.bot.cfg.get("Tokens", {}).get("youtube", None)
    if not token:
        return "YT Token is not configured"

    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"https://www.googleapis.com/youtube/v3/videos?id={video_id}&key={token}&part=snippet"
        ) as r:
            if r.ok:
                _ = await r.json()
                description = _["items"][0]["snippet"]["description"]
            else:
                return "Couldn't find provided video. Is it a valid YT URL with a description?"

    if not description:
        return "Description is missing"

    elapsed = {}

    for line in description.splitlines():
        if not line:
            continue
        _ = CHAPTER_PATTERN.search(line)

        if not _:
            continue
        minute, second, name, checkpoint = _.groups()

        if name not in elapsed:
            elapsed[name] = []

        elapsed[name].append(Chapter(minute, second, checkpoint))

    elapsed = [elapsed[challenge][-1].timestamp - elapsed[challenge][0].timestamp for challenge in elapsed]
    total = sum([i.total_seconds() for i in elapsed])
    if total <= 0:
        return f"Your chapter timestamps are either wrong or malformed as total time is {total} seconds"
    return f"Total time for [{achievement}]({url}) is {timedelta(seconds=total)}"
