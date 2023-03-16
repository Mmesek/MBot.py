from datetime import datetime, timedelta, timezone
from typing import Optional

import sqlalchemy as sa
from MFramework import Context, Discord_Paths, Groups
from MFramework.database.alchemy.mixins import ServerID, Snowflake
from MFramework.database.alchemy.types import Permissions
from mlib.database import ID, Base, Timestamp
from mlib.localization import secondsToText


class Types(Permissions):
    """Infraction Types"""

    Warn: Groups.HELPER = 0
    "Warns user"
    Timeout: Groups.HELPER = 1
    "Timeouts user"
    Mute: Groups.MODERATOR = 1
    Temp_Mute: Groups.MODERATOR = 1
    Unmute: Groups.MODERATOR = 6
    Kick: Groups.MODERATOR = 2
    "Kicks user"
    Ban: Groups.MODERATOR = 3
    "Bans user"
    Temp_Ban: Groups.MODERATOR = 3
    Unban: Groups.ADMIN = 4
    "Unbans user"
    Report: Groups.GLOBAL = 5
    "Reports user"
    Note: Groups.HELPER = 6
    """Note about user"""


class Infraction(Timestamp, ServerID, ID, Base):
    """Infraction object"""

    user_id: Snowflake = sa.Column(
        sa.BigInteger,
        nullable=False
        # sa.ForeignKey("User.id", ondelete="SET DEFAULT", onupdate="Cascade"), nullable=False, default=0
    )
    """ID of User that is infracted"""
    moderator_id: Optional[Snowflake] = sa.Column(
        sa.BigInteger,
        nullable=False
        # sa.ForeignKey("User.id", ondelete="SET DEFAULT", onupdate="Cascade"), nullable=True, default=0
    )
    """ID of Moderator that issued this infraction"""

    type: Types = sa.Column(sa.Enum(Types))
    """`Infractions` type of this infraction"""
    reason: Optional[str] = sa.Column(sa.UnicodeText, nullable=True)
    """Reason of this infraction"""
    duration: Optional[timedelta] = sa.Column(sa.Interval, nullable=True)
    """How long this infraction should be valid/active"""

    channel_id: Optional[Snowflake] = sa.Column(sa.BigInteger, nullable=True)
    """Channel where this infraction happened"""
    message_id: Optional[Snowflake] = sa.Column(sa.BigInteger, nullable=True)
    """Message that caused this infraction (or moderator message that issued infraction)"""
    expires_at: Optional[datetime] = sa.Column(sa.TIMESTAMP(timezone=True), nullable=True)
    """When this infraction was added"""
    weight: float = sa.Column(sa.Float, nullable=False, default=1)
    """Weight of this infraction"""

    def as_string(self, ctx: Context, width: int, id_width: int):
        return (
            ctx.t(
                "row",
                width=width,
                id_width=id_width,
                link="[#](<{}>)".format(
                    Discord_Paths.MessageLink.link.format(
                        guild_id=self.server_id,
                        channel_id=self.channel_id,
                        message_id=self.message_id,
                    )
                )
                if self.message_id
                else "#",
                timestamp=int(self.timestamp.timestamp()),
                reason=self.reason,
                moderator_id=self.moderator_id,
                duration=ctx.t(
                    "for_duration",
                    duration=secondsToText(int(self.duration.total_seconds()), ctx.language),
                )
                if self.duration
                else "",
                active="~~"
                if (self.expires_at and self.expires_at <= datetime.now(tz=timezone.utc))
                and self.type
                not in {
                    Types.Timeout,
                    Types.Unban,
                    Types.Report,
                }
                else "",
            )
            .format(type=ctx.t(self.type.name), id=self.id)
            .strip()
        )
