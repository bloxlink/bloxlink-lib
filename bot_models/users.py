from typing import Self
import hikari
from attrs import field
from .base import BaseModel


class RobloxUser(BaseModel): # pylint: disable=too-many-instance-attributes
    """Representation of a user on Roblox."""

    id: str = field(converter=str)
    username: str = None
    banned: bool = None
    age_days: int = None
    groups: dict = None
    avatar: str = None
    description: str = None
    profile_link: str = None
    display_name: str = None
    created: str = None
    badges: list = None
    short_age_string: str = None
    flags: int = None
    overlay: int = None

    complete: bool = False

    _data: dict = field(factory=lambda: {})


class MemberSerializable(hikari.Member, BaseModel):
    id: int = field(converter=int)
    username: str = None
    avatar_url: str = None
    display_name: str = None
    is_bot: bool = None
    joined_at: str = None
    role_ids: list[int] = None
    guild_id: int = None
    avatar_hash: str = None
    nickname: str = None

    @staticmethod
    def from_hikari(member: hikari.Member) -> Self:
        """Convert a Hikari member into a MemberSerializable object."""

        return MemberSerializable(
            id=member.id,
            username=member.username,
            avatar_url=member.avatar_url,
            display_name=member.display_name,
            is_bot=member.is_bot,
            joined_at=member.joined_at.isoformat(),
            role_ids=member.role_ids,
            guild_id=member.guild_id,
            avatar_hash=member.avatar_hash,
            nickname=member.nickname
        )

    def to_dict(self) -> dict[str, str | int]:
        """Convert the object into a dict of values."""

        return {
            "id": self.id,
            "username": self.username,
            "avatar_url": self.avatar_url,
            "display_name": self.display_name,
            "is_bot": self.is_bot,
            "joined_at": self.joined_at.isoformat(),
            "role_ids": self.role_ids,
            "nick": self.nick,
            "guild_id": self.guild_id,
            "avatar_hash": self.avatar_hash,
        }
