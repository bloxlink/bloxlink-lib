from typing import Mapping, Self, Type, Literal, Annotated
from pydantic import Field, field_validator
import hikari
from .base import Snowflake, BaseModel
import bloxlink_lib.models.binds as binds_module


class UserInfoFieldMapping(BaseModel):
    """Map a field from Bloxlink-expected to developer-expected"""

    robloxID: str = "robloxID"
    guildID: str = "guildID"
    discordID: str = "discordID"
    robloxUsername: str = "robloxUsername"
    discordUsername: str = "discordUsername"


class UserInfoWebhook(BaseModel):
    """Webhook settings for the userInfo webhook"""

    url: str
    fieldMapping: UserInfoFieldMapping = None


class Webhooks(BaseModel):
    """Fired when certain actions happen on Bloxlink"""

    authentication: str

    userInfo: UserInfoWebhook = None


class GroupLock(BaseModel):
    """Group lock settings for a group"""

    groupName: str = None
    dmMessage: str | None = None
    roleSets: Annotated[list[int], Field(default_factory=list)]
    verifiedAction: Literal["kick", "dm"] = "kick"
    unverifiedAction: Literal["kick", "dm"] = "kick"


type MagicRoleTypes = Literal["Bloxlink Admin",
                              "Bloxlink Updater", "Bloxlink Bypass"]


class GuildData(BaseModel):
    """Representation of the stored settings for a guild"""

    id: int
    binds: Annotated[list[binds_module.GuildBind], Field(default_factory=list)]

    @field_validator("binds", mode="before")
    @classmethod
    def transform_binds(cls: Type[Self], binds: list) -> list[binds_module.GuildBind]:
        if all(isinstance(b, binds_module.GuildBind) for b in binds):
            return binds

        return [binds_module.GuildBind(**b) for b in binds]

    verifiedRoleEnabled: bool = True
    verifiedRoleName: str | None = "Verified"  # deprecated
    verifiedRole: str = None

    unverifiedRoleEnabled: bool = True
    unverifiedRoleName: str | None = "Unverified"  # deprecated
    unverifiedRole: str = None

    verifiedDM: str = ":wave: Welcome to **{server-name}**, {roblox-name}! Visit <{verify-url}> to change your account.\nFind more Roblox Communities at https://blox.link/communities !"

    ageLimit: int = None
    autoRoles: bool = True
    autoVerification: bool = True
    disallowAlts: bool | None = False
    disallowBanEvaders: bool | None = False
    banRelatedAccounts: bool | None = False
    unbanRelatedAccounts: bool | None = False
    dynamicRoles: bool | None = True
    groupLock: dict[str, GroupLock] = None
    highTrafficServer: bool = False
    allowOldRoles: bool = False

    webhooks: Webhooks = None

    hasBot: bool = False
    proBot: bool = False

    nicknameTemplate: str = "{smart-name}"
    unverifiedNickname: str = ""

    magicRoles: dict[str, list[MagicRoleTypes]] = None

    premium: dict = Field(default_factory=dict)  # deprecated

    # Old bind fields.
    roleBinds: dict = None
    groupIDs: dict = None
    migratedBindsToV4: bool = False

    def model_post_init(self, __context):
        # merge verified roles into binds
        if self.verifiedRole:
            verified_role_bind = binds_module.GuildBind(
                criteria={"type": "verified"}, roles=[self.verifiedRole])

            if verified_role_bind not in self.binds:
                self.binds.append(verified_role_bind)

        if self.unverifiedRole:
            unverified_role_bind = binds_module.GuildBind(
                criteria={"type": "unverified"}, roles=[self.unverifiedRole])

            if unverified_role_bind not in self.binds:
                self.binds.append(unverified_role_bind)

        # # convert old binds
        # if self.roleBinds and not self.converted_binds:
        #     self.converted_binds = True

        #     for role_id, group_id in self.roleBinds.items():
        #         self.binds.append(binds_module.GuildBind(criteria={"type": "group", "group_id": group_id}, roles=[role_id]))

        #     self.roleBinds = None


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


# RoleSerializable is not defined when the schema is first built, so we need to re-build it. TODO: make better
binds_module.GuildBind.model_rebuild()
