from typing import Mapping, Self, Type
from pydantic import Field, field_validator
import hikari
from .base import Snowflake, BaseModel
import bloxlink_lib.models.binds as binds_module


class GuildData(BaseModel):
    """Representation of the stored settings for a guild"""

    id: int
    binds: list[binds_module.GuildBind] = Field(default_factory=list)

    @field_validator("binds", mode="before")
    @classmethod
    def transform_binds(cls: Type[Self], binds: list) -> list[binds_module.GuildBind]:
        return [binds_module.GuildBind(**b) for b in binds]


    verifiedRoleEnabled: bool = True
    verifiedRoleName: str = "Verified"  # deprecated
    verifiedRole: str = None

    unverifiedRoleEnabled: bool = True
    unverifiedRoleName: str = "Unverified"  # deprecated
    unverifiedRole: str = None

    ageLimit: int = None
    autoRoles: bool = True
    autoVerification: bool = True
    disallowAlts: bool = False
    disallowBanEvaders: str = False  # Site sets it to "ban" when enabled. Null when disabled.
    dynamicRoles: bool = True
    groupLock: dict = None
    highTrafficServer: bool = False
    allowOldRoles: bool = False

    nicknameTemplate: str = "{smart-name}"

    premium: dict = Field(default_factory=dict) # deprecated

    affiliate: dict = None # deprecated

    # Old bind fields.
    roleBinds: dict = None
    groupIDs: dict = None
    converted_binds: bool = False

    def model_post_init(self, __context):
        # merge verified roles into binds
        if self.verifiedRole:
            self.binds.append(binds_module.GuildBind(criteria={"type": "verified"}, roles=[self.verifiedRole]))

        if self.unverifiedRole:
            self.binds.append(binds_module.GuildBind(criteria={"type": "unverified"}, roles=[self.unverifiedRole]))

        # if self.verifiedRoleName:
        #     self.binds.append(GuildBind(criteria={"type": "verified"}, roles=[self.verifiedRole]))


class RoleSerializable(BaseModel):
    id: Snowflake
    name: str = None
    color: int = None
    is_hoisted: bool = None
    position: int = None
    permissions: Snowflake = None
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

class GuildSerializable(BaseModel):
    id: Snowflake
    name: str = None
    roles: Mapping[Snowflake, RoleSerializable] = Field(default_factory=dict)

    @field_validator("roles", mode="before")
    @classmethod
    def transform_roles(cls: Type[Self], roles: list) -> Mapping[Snowflake, RoleSerializable]:
        return {int(r_id): RoleSerializable.from_hikari(r) for r_id, r in roles.items()}

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

binds_module.GuildBind.model_rebuild() # RoleSerializable is not defined when the schema is first built, so we need to re-build it. TODO: make better
