from typing import Self
from attrs import define, field
import hikari
from .base import BaseModel


@define(slots=True)
class GuildData:
    """Representation of the stored settings for a guild"""

    id: int
    binds: list = field(factory=list)

    verifiedRoleEnabled: bool = True
    verifiedRoleName: str = "Verified"  # deprecated
    verifiedRole: str = None

    unverifiedRoleEnabled: bool = True
    unverifiedRoleName: str = "Unverified"  # deprecated
    unverifiedRole: str = None

    ageLimit: int = None
    autoRoles: bool = None
    autoVerification: bool = None
    disallowAlts: bool = None
    disallowBanEvaders: str = None  # Site sets it to "ban" when enabled. Null when disabled.
    dynamicRoles: bool = None
    groupLock: dict = None
    highTrafficServer: bool = None

    nicknameTemplate: str = "{smart-name}"

    premium: dict = field(factory=dict) # deprecated

    affiliate: dict = None

    # Old bind fields.
    roleBinds: dict = None
    groupIDs: dict = None
    converted_binds: bool = False

@define(kw_only=True)
class GuildSerializable(BaseModel):
    id: int = field(converter=int)
    name: str = None
    roles: dict[int, hikari.Role] = None

    @staticmethod
    def from_hikari(guild: hikari.RESTGuild) -> Self:
        """Convert a Hikari guild into a GuildSerializable object."""

        return GuildSerializable(
            id=guild.id,
            name=guild.name,
            roles=guild.roles
        )
