from typing import Sequence, Self
import hikari
from attrs import field, define
from .base import BaseModel


@define(slots=True)
class UserData:
    """Representation of a User's data in Bloxlink

    Attributes:
        id (int): The Discord ID of the user.
        robloxID (str): The roblox ID of the user's primary account.
        robloxAccounts (dict): All of the user's linked accounts, and any guild specific verifications.
    """

    id: int
    robloxID: str = None
    robloxAccounts: dict = field(factory=lambda: {"accounts": [], "guilds": {}, "confirms": {}})


@define(kw_only=True)
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


@define(kw_only=True)
class MemberSerializable(BaseModel):
    id: hikari.Snowflake = field(converter=int)
    username: str = None
    avatar_url: str = None
    display_name: str = None
    is_bot: bool = None
    joined_at: str = None
    role_ids: Sequence[hikari.Snowflake] = None
    guild_id: int = None
    avatar_hash: str = None
    nickname: str = None

    @staticmethod
    def from_hikari(member: hikari.InteractionMember | Self) -> 'MemberSerializable':
        """Convert a Hikari member into a MemberSerializable object."""

        if isinstance(member, MemberSerializable):
            return member

        return MemberSerializable(
            id=member.id,
            username=member.username,
            avatar_url=str(member.avatar_url),
            display_name=member.display_name,
            is_bot=member.is_bot,
            joined_at=member.joined_at,
            role_ids=member.role_ids,
            guild_id=member.guild_id,
            avatar_hash=member.avatar_hash,
            nickname=member.nickname
        )
