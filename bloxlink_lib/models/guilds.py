from typing import Mapping, Self
from attrs import define, field
import hikari
from .base import BaseModel
from .binds import GuildBind, get_binds


@define(slots=True)
class GuildData:
    """Representation of the stored settings for a guild"""

    id: int
    binds: list[GuildBind] = field(converter=lambda binds: [GuildBind(**b) for b in binds])

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

    def __attrs_post_init__(self):
        # merge verified roles into binds
        if self.verifiedRole:
            self.binds.append(GuildBind(criteria={"type": "verified"}, roles=[self.verifiedRole]))

        if self.unverifiedRole:
            self.binds.append(GuildBind(criteria={"type": "unverified"}, roles=[self.unverifiedRole]))


@define(kw_only=True)
class RoleSerializable(BaseModel):
    id: hikari.Snowflake = field(converter=int)
    name: str = None
    color: int = None
    is_hoisted: bool = None
    position: int = None
    permissions: hikari.Permissions = None
    is_managed: bool = None
    is_mentionable: bool = None

    @staticmethod
    def from_hikari(role: hikari.Role | Self) -> 'RoleSerializable':
        """Convert a Hikari role into a RoleSerializable object."""

        if isinstance(role, RoleSerializable):
            return role

        return RoleSerializable(
            id=role.id,
            name=role.name,
            color=role.color,
            is_hoisted=role.is_hoisted,
            position=role.position,
            permissions=role.permissions,
            is_managed=role.is_managed,
            is_mentionable=role.is_mentionable
        )

@define(kw_only=True)
class GuildSerializable(BaseModel):
    id: hikari.Snowflake = field(converter=int)
    name: str = None
    roles: Mapping[hikari.Snowflake, RoleSerializable] = field(converter=lambda roles: {int(r_id): RoleSerializable.from_hikari(r).to_dict() for r_id, r in roles.items()})

    @staticmethod
    def from_hikari(guild: hikari.RESTGuild | Self) -> 'GuildSerializable':
        """Convert a Hikari guild into a GuildSerializable object."""

        if isinstance(guild, GuildSerializable):
            return guild

        return GuildSerializable(
            id=guild.id,
            name=guild.name,
            roles=guild.roles
        )
