from __future__ import annotations

import re
import math
from typing import TYPE_CHECKING, Any, Literal, NotRequired, TypedDict

from pydantic import Field, ValidationError

import bloxlink_lib.database as database

from ..models.base import BaseModel, CoerciveSet, RobloxEntity, SnowflakeSet, create_entity
from ..utils import find

if TYPE_CHECKING:
    from hikari import Member

    from .assets import RobloxAsset
    from .groups import RobloxGroup
    from .guilds import RoleSerializable
    from .users import MemberSerializable, RobloxUser

POP_OLD_BINDS: bool = False

VALID_BIND_TYPES = Literal["group", "catalogAsset", "badge", "gamepass", "verified", "unverified"]
ARBITRARY_GROUP_TEMPLATE = re.compile(r"\{group-rank-(.*?)\}")
NICKNAME_TEMPLATE_REGEX = re.compile(r"\{(.*?)\}")


# TypedDict definitions used for function kwargs
class GroupBindDataDict(TypedDict, total=False):
    everyone: bool
    guest: bool
    min: int
    max: int
    roleset: int
    dynamicRoles: bool


class BindCriteriaDict(TypedDict):
    type: VALID_BIND_TYPES
    id: NotRequired[int]
    group: NotRequired[GroupBindData]


class BindDataDict(TypedDict):
    displayName: str


# Pydantic definitions
class GroupBindData(BaseModel):
    """Represents the data required for a group bind."""

    # conditions
    everyone: bool = False
    guest: bool = False
    min: int = None
    max: int = None
    roleset: int = None
    ####################

    dynamicRoles: bool = False  # full group bind

    def model_post_init(self, __context: Any) -> None:
        if (self.min or self.max) and not all([self.min, self.max]):
            raise ValidationError("Both min and max range must be set.")

        if self.roleset and (self.min or self.max):
            raise ValidationError("Either a Roleset or range can be set.")

        if self.everyone and (self.guest or self.min or self.max or self.roleset):
            raise ValidationError("Everyone condition cannot have any other conditions.")


class BindCriteria(BaseModel):
    """Represents the criteria required for a bind. If anything is set, it must ALL be met."""

    type: VALID_BIND_TYPES
    id: int | None = Field(default=None)

    group: GroupBindData | None = None


class BindData(BaseModel):
    """Represents the data required for a bind."""

    displayName: str = None


class GuildBind(BaseModel):
    """Represents a role binding from the database.

    Attributes:
        nickname (str, optional): The nickname template to be applied to users. Defaults to None.
        roles (list): The IDs of roles that should be given by this bind.
        removeRole (list): The IDs of roles that should be removed when this bind is given.

        criteria (BindCriteria): Bind-specific requirements

        entity (RobloxEntity, optional): The entity that this binding represents. Defaults to None.
    """

    # Fields from the database.
    nickname: str | None = None
    roles: list[str] = Field(default_factory=list)
    remove_roles: list[str] = Field(default_factory=list, alias="removeRoles")

    criteria: BindCriteria
    data: BindData | None = Field(default=None)

    # Excluded fields. These are used for the bind algorithms.
    pending_new_roles: list[str] = Field(exclude=True, default_factory=list)
    entity: RobloxEntity | None = Field(exclude=True, default=None)
    type: Literal["group", "catalogAsset", "badge", "gamepass", "verified", "unverified"] | None = Field(
        exclude=True, default=None
    )
    subtype: Literal["role_bind", "full_group"] | None = Field(exclude=True, default=None)
    highest_role: RoleSerializable | None = Field(exclude=True, default=None)  # highest role in the guild

    def model_post_init(self, __context):
        self.entity = self.entity or create_entity(self.criteria.type, self.criteria.id)
        self.type = self.criteria.type

        if self.type == "group":
            self.subtype = "full_group" if self.criteria.group.dynamicRoles else "role_bind"

    @classmethod
    def from_V3(
        cls,
        bind_type: Literal["groupIDs", "assets", "badges", "gamePasses"],
        bind_id: str | int,
        bind_data: dict,
    ):
        converted_data = {}

        match bind_type:
            case "groupIDs":
                # Whole group binds
                bind_criteria = {
                    "type": "group",
                    "id": bind_id,
                    "group": {"dynamicRoles": True},
                }
                converted_data = {
                    "nickname": bind_data.get("nickname") or None,
                    "criteria": bind_criteria,
                    "remove_roles": bind_data.get("removeRoles") or [],
                    "data": {"displayName": bind_data.get("groupName")},
                }

            case "assets" | "badges" | "gamePasses":
                # All non group rolebinds
                if bind_type == "gamePasses":
                    bind_type = "gamepass"
                elif bind_type == "assets":
                    bind_type = "catalogAsset"
                else:
                    bind_type = bind_type[:-1]

                converted_data = {
                    "nickname": bind_data.get("nickname") or None,
                    "roles": bind_data.get("roles") or [],
                    "remove_roles": bind_data.get("removeRoles") or [],
                    "criteria": {
                        "type": bind_type,
                        "id": bind_id,
                    },
                    "data": {"displayName": bind_data.get("displayName")},
                }

        return cls(**converted_data)

    @classmethod
    def from_V3_group_rolebind(
        cls, bind_type: Literal["roleset", "range"], bind_id: int | str, bind_data: dict
    ):
        converted_data = {}

        match bind_type:
            case "roleset":
                roleset_id, roleset_data = next(iter(bind_data.items()))
                group_criteria_data = {}

                if roleset_id == "all":
                    group_criteria_data["everyone"] = True
                elif roleset_id == "0":
                    group_criteria_data["guest"] = True
                else:
                    group_criteria_data["roleset"] = int(roleset_id)

                converted_data = {
                    "nickname": roleset_data.get("nickname"),
                    "roles": roleset_data.get("roles") or [],
                    "remove_roles": roleset_data.get("removeRoles") or [],
                    "criteria": {
                        "type": "group",
                        "id": bind_id,
                        "group": group_criteria_data,
                    },
                }

            case "range":
                converted_data = {
                    "nickname": bind_data.get("nickname"),
                    "roles": bind_data.get("roles") or [],
                    "remove_roles": bind_data.get("removeRoles") or [],
                    "criteria": {
                        "type": "group",
                        "id": bind_id,
                        "group": {
                            "min": bind_data.get("low"),
                            "max": bind_data.get("high"),
                        },
                    },
                }

        return cls(**converted_data)

    def calculate_highest_role(self, guild_roles: dict[str, RoleSerializable]) -> None:
        """Calculate the highest role in the guild for this bind."""

        if self.roles and not self.highest_role:
            filtered_binds = filter(
                lambda r: str(r.id) in self.roles and self.nickname, guild_roles.values()
            )  # pylint: disable=unsupported-membership-test

            if len(list(filtered_binds)):
                self.highest_role = max(filtered_binds, key=lambda r: r.position)

    async def satisfies_for(
        self,
        guild_roles: dict[int, RoleSerializable],
        member: Member | MemberSerializable,
        roblox_user: RobloxUser | None = None,
    ) -> tuple[bool, SnowflakeSet, CoerciveSet[str], SnowflakeSet]:
        """Check if a user satisfies the requirements for this bind."""

        ineligible_roles = SnowflakeSet()
        additional_roles = SnowflakeSet()
        missing_roles = CoerciveSet(str)

        if not roblox_user:
            if self.criteria.type == "unverified":
                return True, additional_roles, missing_roles, ineligible_roles

            # user is unverified, so remove Verified role
            if self.criteria.type == "verified":
                for role_id in filter(lambda r: int(r) in member.role_ids, self.roles):
                    ineligible_roles.add(role_id)

            return False, additional_roles, missing_roles, ineligible_roles

        # user is verified
        match self.criteria.type:
            case "verified":
                return True, additional_roles, missing_roles, ineligible_roles

            case "group":
                group: RobloxGroup = self.entity

                await group.sync_for(roblox_user, sync=True)

                user_roleset = group.user_roleset

                # check if the user has any group roleset roles they shouldn't have
                if self.criteria.group.dynamicRoles:
                    for roleset in group.rolesets.values():
                        for role_id in member.role_ids:
                            if (
                                role_id in guild_roles
                                and guild_roles[role_id].name == roleset.name
                                and str(roleset) != str(user_roleset)
                            ):
                                ineligible_roles.add(role_id)

                if self.criteria.id in roblox_user.groups:
                    # full group bind. check for a matching roleset
                    if self.criteria.group.dynamicRoles:
                        roleset_role = find(lambda r: r.name == user_roleset.name, guild_roles.values())

                        if roleset_role:
                            additional_roles.add(roleset_role.id)
                        else:
                            missing_roles.add(user_roleset.name)

                    if self.criteria.group.everyone:
                        return True, additional_roles, missing_roles, ineligible_roles

                    if self.criteria.group.guest:
                        return False, additional_roles, missing_roles, ineligible_roles

                    if (self.criteria.group.min and self.criteria.group.max) and (
                        self.criteria.group.min <= group.user_roleset.rank <= self.criteria.group.max
                    ):
                        return True, additional_roles, missing_roles, ineligible_roles

                    if self.criteria.group.roleset:
                        roleset = self.criteria.group.roleset
                        return (
                            group.user_roleset.rank == roleset
                            or (roleset < 0 and group.user_roleset.rank >= abs(roleset)),
                            additional_roles,
                            missing_roles,
                            ineligible_roles,
                        )

                    # TODO: Why do we fail positive here if our checks don't match up?
                    return True, additional_roles, missing_roles, ineligible_roles

                # Not in the group.
                # Return whether the bind is for guests only
                return self.criteria.group.guest, additional_roles, missing_roles, ineligible_roles

            case "badge" | "gamepass" | "catalogAsset":
                asset: RobloxAsset = self.entity

                return await roblox_user.owns_asset(asset), additional_roles, missing_roles, ineligible_roles

        return False, additional_roles, missing_roles, ineligible_roles

    @property
    def description_prefix(self) -> str:
        """Generate the prefix string for a bind's description.

        Returns:
            str: The prefix string for a bind's description.
        """

        match self.type:
            case "group":
                if self.criteria.group.min and self.criteria.group.max:
                    return "People with a rank between"

                if self.criteria.group.min and self.criteria.group.max:
                    return "People with a rank in-between the range"

                if self.criteria.group.roleset:
                    if self.criteria.group.roleset < 0:
                        return "People with a rank greater than or equal to"

                    return "People with the rank"

                if self.criteria.group.guest:
                    return "People who are NOT in **this group**"

                if self.criteria.group.everyone:
                    return "People who are in **this group**"

            case "verified":
                return "People who have verified their Roblox account"

            case "unverified":
                return "People who have not verified their Roblox account"

            case _:
                return f"People who own the {self.type}"

    @property
    def description_content(self) -> str:
        """Generate the content string for a bind's description.

        This will be the content that describes the rolesets to be given,
        or the name of the other entity that the bind is for.

        Returns:
            str: The content string for a bind's description.
                Roleset bindings like guest and everyone do not have content to display,
                as the given prefix string contains the content.
        """

        content: str = None

        match self.type:
            case "group":
                group: RobloxGroup = self.entity

                if self.criteria.group.min and self.criteria.group.max:
                    content = f"{group.roleset_name_string(self.criteria.group.min, bold_name=False)} to {group.roleset_name_string(self.criteria.group.max, bold_name=False)}"

                elif self.criteria.group.roleset:
                    content = group.roleset_name_string(abs(self.criteria.group.roleset), bold_name=False)

            case "verified" | "unverified":
                content = ""

            case _:
                content = str(self.entity).replace("**", "")

        return content

    @property
    def short_description(self) -> str:
        """Similar to str() but does not give details about the roles"""

        if self.type == "group" and self.subtype == "full_group":
            return "All users receive a role matching their group rank name"

        content = self.description_content

        return f"{self.description_prefix}{' ' if content else ''}{f'**{content}**' if content else ''}"

    def __str__(self) -> str:
        """Builds a sentence-formatted string for a binding.

        Results in the layout of: <USERS> <CONTENT ID/RANK> receive the role(s) <ROLE LIST>, and have the roles
        removed <REMOVE ROLE LIST>

        The remove role list is only appended if it there are roles to remove.

        Example output:
            All users in this group receive the role matching their group rank name.
            People with the rank Developers (200) receive the role @a
            People with a rank greater than or equal to Supporter (1) receive the role @b

        Returns:
            str: The sentence description of this binding.
        """

        extended_description = self.short_description

        if self.type == "group" and self.subtype == "full_group":
            return "- _All users in **this** group receive the role matching their group rank name_"  # extended_description is not used in case we want the description to be shorter

        role_mentions = ", ".join(f"<@&{val}>" for val in self.roles)
        remove_role_mentions = ", ".join(f"<@&{val}>" for val in self.remove_roles)
        new_roles_list = ", ".join(f"{val} [NEW]" for val in self.pending_new_roles)

        return (
            f"- _{extended_description} receive the "
            f"role{'s' if len(self.roles) > 1 or len(self.pending_new_roles) > 1 else ''} {role_mentions}{new_roles_list}"
            f"{'' if len(self.remove_roles) == 0 else f', and have these roles removed: {remove_role_mentions}'}_"
        )

    def __eq__(self, other: GuildBind) -> bool:
        return self.criteria == other.criteria


async def build_binds_desc(
    guild_id: int | str,
    bind_id: int | str = None,
    bind_type: VALID_BIND_TYPES = None,
) -> str:
    """Get a string-based representation of all bindings (matching the bind_id and bind_type).

    Output is limited to 5 bindings, after that the user is told to visit the website to see the rest.

    Args:
        guild_id (int | str): ID of the guild.
        bind_id (int | str, optional): The entity ID to filter binds from. Defaults to None.
        bind_type (ValidBindType, optional): The type of bind to filter the response by.
            Defaults to None.

    Returns:
        str: Sentence representation of the first five binds matching the filters.
    """

    guild_binds = await get_binds(guild_id, category=bind_type, bind_id=bind_id)

    # sync the first 5 binds
    for bind in guild_binds[:5]:
        await bind.entity.sync()

    bind_strings = [str(bind) for bind in guild_binds[:5]]
    output = "\n".join(bind_strings)

    if len(guild_binds) > 5:
        output += (
            f"\n_... and {len(guild_binds) - 5} more. "
            f"Click [here](https://www.blox.link/dashboard/guilds/{guild_id}/binds) to view the rest!_"
        )
    return output


async def count_binds(guild_id: int | str, bind_id: int = None) -> int:
    """Count the number of binds that this guild_id has created.

    Args:
        guild_id (int | str): ID of the guild.
        bind_id (int, optional): ID of the entity to filter by when counting. Defaults to None.

    Returns:
        int: The number of bindings this guild has created.
    """

    guild_data = await get_binds(guild_id)

    return len(guild_data) if not bind_id else sum(1 for b in guild_data if b.id == int(bind_id)) or 0


async def get_binds(
    guild_id: int | str,
    category: VALID_BIND_TYPES = None,
    bind_id: int = None,
    guild_roles: dict[int, RoleSerializable] = None,
) -> list[GuildBind]:
    """Get the current guild binds.

    Old binds will be included by default, but will not be saved in the database in the
    new format unless the POP_OLD_BINDS flag is set to True. While it is False, old formatted binds will
    be left as is.
    """

    guild_id = str(guild_id)

    # Migrate any old bindings before we get the current binds.
    await migrate_old_binds(guild_id)

    guild_data = await database.fetch_guild_data(
        guild_id,
        "binds",
        "verifiedRole",
        "unverifiedRole",
        "verifiedRoleName",
        "unverifiedRoleName",
        "unverifiedRoleEnabled",
        "unverifiedRoleEnabled",
    )  # some are needed to polyfill the binds

    # check the guild roles for a verified role
    if (
        guild_roles
        and (guild_data.unverifiedRoleEnabled or guild_data.verifiedRoleEnabled)
        and not any(b.criteria.type == "verified" for b in guild_data.binds)
    ):
        verified_role_name = guild_data.verifiedRoleName
        unverified_role_name = guild_data.unverifiedRoleName
        verified_role_enabled = guild_data.verifiedRoleEnabled
        unverified_role_enabled = guild_data.unverifiedRoleEnabled

        if verified_role_name or unverified_role_name:
            for role in guild_roles.values():
                if verified_role_enabled and role.name == verified_role_name:
                    guild_data.binds.append(
                        GuildBind(
                            criteria=BindCriteria(type="verified"),
                            roles=[str(role.id)],
                        )
                    )
                elif unverified_role_enabled and role.name == unverified_role_name:
                    guild_data.binds.append(
                        GuildBind(
                            criteria=BindCriteria(type="unverified"),
                            roles=[str(role.id)],
                        )
                    )

    return list(
        filter(
            lambda b: b.type == category and ((bind_id and b.criteria.id == bind_id) or not bind_id),
            guild_data.binds,
        )
        if category
        else guild_data.binds
    )


async def get_nickname_template(guild_id, potential_binds: list[GuildBind]) -> tuple[str, GuildBind | None]:
    """Get the unparsed nickname template for the user."""

    guild_data = await database.fetch_guild_data(
        guild_id,
        "nicknameTemplate",
    )

    # first sort the binds by role position
    potential_binds.sort(
        key=lambda b: b.highest_role.position if b.highest_role else math.inf, reverse=True
    )  # arbitrary big number

    highest_priority_bind: GuildBind = potential_binds[0] if potential_binds else None

    nickname_template = (
        highest_priority_bind.nickname
        if highest_priority_bind and highest_priority_bind.nickname
        else guild_data.nicknameTemplate
    )

    return nickname_template, highest_priority_bind


async def parse_template(
    guild_id: int,
    guild_name: str,
    member: Member | MemberSerializable,
    template: str = None,
    potential_binds: list[GuildBind] | None = None,
    roblox_user: RobloxUser | None = None,
    max_length=True,
) -> str | None:
    """
    Parse the template for the user.

    The algorithm is as follows:
    - Find the highest priority bind that has a nickname. The priority is determined by the position of the role in the guild.
    - If no such bind is found, the template is guild_data.nicknameTemplate.

    The template is then adjusted to the user's data.
    """

    highest_priority_bind: GuildBind | None = None
    smart_name: str = ""
    group_bind: GuildBind | None = None

    if not template:
        if not guild_id or potential_binds is None:
            raise ValueError("Guild ID and potential binds must be provided if no template is given.")

        # this is for nickname calculation
        template, highest_priority_bind = await get_nickname_template(guild_id, potential_binds)

    if template == "{disable-nicknaming}":
        return None

    # if the template contains a group template, sync the group
    if "group-" in template:
        # get the group from the highest bind if it's a group bind; otherwise, find the first linked group bind
        group_bind = (
            highest_priority_bind
            if highest_priority_bind and highest_priority_bind.type == "group"
            else find(lambda b: b.type == "group", potential_binds)
        )

        if group_bind:
            await group_bind.entity.sync()

    # parse {smart-name}
    if roblox_user:
        if roblox_user.display_name != roblox_user.username:
            smart_name = f"{roblox_user.display_name} (@{roblox_user.username})"

            if len(smart_name) > 32:
                smart_name = roblox_user.username
        else:
            smart_name = roblox_user.username

        # parse {group-rank}
        if roblox_user:
            if "group-rank" in template:
                if group_bind and group_bind.criteria.id in roblox_user.groups:
                    if highest_priority_bind:
                        group_roleset_name = roblox_user.groups[highest_priority_bind.criteria.id].role.name
                    else:
                        group_roleset_name = roblox_user.groups[potential_binds[0].criteria.id].role.name
                else:
                    group_roleset_name = "Guest"
            else:
                group_roleset_name = "Guest"

            # parse {group-rank-<group_id>} in the nickname template
            for group_id in ARBITRARY_GROUP_TEMPLATE.findall(template):
                group = roblox_user.groups.get(group_id)
                group_role_from_group = group.role.name if group else "Guest"

                template = template.replace("{group-rank-" + group_id + "}", group_role_from_group)

    # parse the nickname template
    for outer_nick in NICKNAME_TEMPLATE_REGEX.findall(template):
        nick_data = outer_nick.split(":")
        nick_fn: str | None = nick_data[0] if len(nick_data) > 1 else None
        nick_value: str = nick_data[1] if len(nick_data) > 1 else nick_data[0]

        # nick_fn = capA
        # nick_value = roblox-name

        if roblox_user:
            match nick_value:
                case "roblox-name":
                    nick_value = roblox_user.username
                case "display-name":
                    nick_value = roblox_user.display_name
                case "smart-name":
                    nick_value = smart_name
                case "roblox-id":
                    nick_value = str(roblox_user.id)
                case "roblox-age":
                    nick_value = str(roblox_user.age_days)
                case "group-rank":
                    nick_value = group_roleset_name

        match nick_value:
            case "discord-name":
                nick_value = member.username
            case "discord-nick":
                nick_value = member.nickname if member.nickname else member.username
            case "discord-mention":
                nick_value = member.mention
            case "discord-id":
                nick_value = str(member.id)
            case "server-name":
                nick_value = guild_name
            case "prefix":
                nick_value = "/"
            case "group-url":
                nick_value = group_bind.entity.url if group_bind else ""
            case "group-name":
                nick_value = group_bind.entity.name if group_bind else ""
            case "smart-name":
                nick_value = smart_name
            case "verify-url":
                nick_value = "https://blox.link/verify"

        if nick_fn:
            if nick_fn in ("allC", "allL"):
                if nick_fn == "allC":
                    nick_value = nick_value.upper()
                elif nick_fn == "allL":
                    nick_value = nick_value.lower()

                template = template.replace("{{{0}}}".format(outer_nick), nick_value)
            else:
                template = template.replace("{{{0}}}".format(outer_nick), outer_nick)  # remove {} only
        else:
            template = template.replace("{{{0}}}".format(outer_nick), nick_value)

    if max_length:
        return template[:32]

    return template


async def migrate_old_binds(guild_id: str):
    """Migrates binds from the V3 structure to V4 and saves them to the database.

    If POP_OLD_BINDS is true, the old binds will be removed from the database.
    """
    guild_data = await database.fetch_guild_data(
        guild_id,
        "binds",
        "roleBinds",
        "groupIDs",
        "converted_binds",
    )

    # Remove old binds and dip, but only if we've migrated already.
    if POP_OLD_BINDS and guild_data.converted_binds:
        await database.update_guild_data(guild_id, groupIDs=None, roleBinds=None, converted_binds=None)
        return

    # We've already migrated, don't try again.
    if guild_data.converted_binds:
        return

    migrated_binds = []
    group_id_binds = guild_data.groupIDs or {}
    rolebinds = guild_data.roleBinds or {}

    # Stop early if there's nothing to do.
    if not group_id_binds and not rolebinds:
        return

    for group_id, bind_data in group_id_binds.items():
        migrated_binds.append(GuildBind.from_V3("groupIDs", group_id, bind_data))

    for bind_type, bindings in rolebinds.items():
        match bind_type:
            case "assets" | "badges" | "gamePasses":
                # Assets, badges, gamePasses
                for entity_id, bind_data in bindings.items():
                    migrated_binds.append(GuildBind.from_V3(bind_type, entity_id, bind_data))

                continue

            case "groups":
                # Single rank bindings + everyone/all + negative binds.
                if bindings.get("binds"):
                    for rank_id, criteria_data in bind_data["binds"].items():
                        migrated_binds.append(
                            GuildBind.from_V3_group_rolebind("roleset", group_id, {rank_id: criteria_data})
                        )

                # Ranges
                if bindings.get("ranges"):
                    for criteria_data in bind_data["ranges"]:
                        migrated_binds.append(
                            GuildBind.from_V3_group_rolebind("range", group_id, criteria_data)
                        )

    if migrated_binds:
        # Removes duplicates
        # TODO: Check efficiency, GuildBind isn't hashable so we can't use sets.
        guild_data.binds.extend(b for b in migrated_binds if b not in guild_data.binds)

        await database.update_guild_data(
            guild_id,
            binds=[b.model_dump(exclude_unset=True, by_alias=True) for b in guild_data.binds],
            converted_binds=True,
        )
