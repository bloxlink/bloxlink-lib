from __future__ import annotations
from typing import Any, Literal, TYPE_CHECKING, TypedDict, NotRequired

from pydantic import Field, ValidationError

from ..models.base import RobloxEntity, create_entity, BaseModel
import bloxlink_lib.database as database
from ..utils import find

if TYPE_CHECKING:
    from .guilds import RoleSerializable
    from .users import MemberSerializable, RobloxUser
    from .groups import RobloxGroup
    from .assets import RobloxAsset

POP_OLD_BINDS: bool = False

VALID_BIND_TYPES = Literal["group", "catalogAsset", "badge", "gamepass", "verified", "unverified"]


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

    dynamicRoles: bool = False # full group bind

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
    entity: RobloxEntity | None = Field(exclude=True, default=None)
    type: Literal["group", "catalogAsset", "badge", "gamepass", "verified", "unverified"] | None = Field(exclude=True, default=None)
    subtype: Literal["role_bind", "full_group"] | None = Field(exclude=True, default=None)
    highest_role: RoleSerializable | None = Field(exclude=True, default=None) # highest role in the guild

    def model_post_init(self, __context):
        self.entity = self.entity or create_entity(self.criteria.type, self.criteria.id)
        self.type = self.criteria.type

        if self.type == "group":
            self.subtype = "full_group" if self.criteria.group.dynamicRoles else "role_bind"

    def calculate_highest_role(self, guild_roles: dict[str, RoleSerializable]) -> None:
        """Calculate the highest role in the guild for this bind."""

        if self.roles and not self.highest_role:
            filtered_binds = filter(lambda r: str(r.id) in self.roles and self.nickname, guild_roles.values()) # pylint: disable=unsupported-membership-test

            if filtered_binds:
                self.highest_role = max(filtered_binds, key=lambda r: r.position)

    async def satisfies_for(self, guild_roles: dict[str, RoleSerializable], member: MemberSerializable, roblox_user: RobloxUser | None = None) -> tuple[bool, list[RoleSerializable], list[str], list[RoleSerializable]]:
        """Check if a user satisfies the requirements for this bind."""

        ineligible_roles: list[str] = []
        additional_roles: list[str] = []
        missing_roles: list[str] = []

        if not roblox_user:
            if self.criteria.type == "unverified":
                return True, additional_roles, missing_roles, ineligible_roles

            # user is unverified, so remove Verified role
            if self.criteria.type == "verified":
                for role_id in filter(lambda r: int(r) in member.role_ids, self.roles):
                    ineligible_roles.append(role_id)

            return False, additional_roles, missing_roles, ineligible_roles


        # user is verified
        match self.criteria.type:
            case "verified":
                return True, additional_roles, missing_roles, ineligible_roles

            case "group":
                group: RobloxGroup = self.entity

                await roblox_user.sync(["groups"])

                if self.criteria.id in roblox_user.groups:
                    # full group bind. check for a matching roleset
                    if self.criteria.group.dynamicRoles:
                        await group.sync_for(roblox_user)

                        user_roleset = group.user_roleset
                        roleset_role = find(lambda r: r.name == user_roleset.name, guild_roles.values())

                        if roleset_role:
                            additional_roles.append(str(roleset_role.id))
                        else:
                            missing_roles.append(user_roleset.name)

                    if self.criteria.group.everyone:
                        return True, additional_roles, missing_roles, ineligible_roles

                    if self.criteria.group.guest:
                        return False, additional_roles, missing_roles, ineligible_roles

                    await group.sync_for(roblox_user)

                    if (self.criteria.group.min and self.criteria.group.max) and (self.criteria.group.min <= group.user_roleset.rank <= self.criteria.group.max):
                        return True, additional_roles, missing_roles, ineligible_roles

                    if self.criteria.group.roleset:
                        roleset = self.criteria.group.roleset
                        return group.user_roleset.rank == roleset or (roleset < 0 and group.user_roleset.rank <= abs(roleset)), additional_roles, missing_roles, ineligible_roles

                    return True, additional_roles, missing_roles, ineligible_roles


                # Not in group.
                # check if the user has any group rolesets they shouldn't have
                if self.criteria.group.dynamicRoles:
                    await group.sync()

                    for roleset in group.rolesets.values():
                        for role_id in member.role_ids:
                            if role_id in guild_roles and guild_roles[role_id].name == roleset.name:
                                ineligible_roles.append(str(role_id))

                # Return whether the bind is for guests only
                return self.criteria.group.guest, additional_roles, missing_roles, ineligible_roles

            case "badge" | "gamepass" | "catalogAsset":
                asset: RobloxAsset = self.entity

                return await roblox_user.owns_asset(asset), additional_roles, missing_roles, ineligible_roles


        return False, additional_roles, missing_roles, ineligible_roles

    @property
    def _prefix(self) -> str:
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
    def _content(self) -> str:
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
                    min_str = group.roleset_name_string(self.criteria.group.min, bold_name=False)
                    max_str = group.roleset_name_string(self.max, bold_name=False)

                    content = f"{min_str}** and **{max_str}"

                elif self.criteria.group.min and self.criteria.group.max:
                    content = f"{group.roleset_name_string(self.criteria.group.min, bold_name=False)} to {group.roleset_name_string(self.criteria.group.max, bold_name=False)}"

                elif self.criteria.group.roleset:
                    content = group.roleset_name_string(abs(self.criteria.group.roleset), bold_name=False)

            case "verified" | "unverified":
                content = ""

            case _:
                content = str(self.entity).replace("**", "")

        return content

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

        if self.type == "group" and self.subtype == "full_group":
            return "- _All users in **this** group receive the role matching their group rank name._"

        role_mentions = ", ".join(f"<@&{val}>" for val in self.roles)
        remove_role_mentions = ", ".join(f"<@&{val}>" for val in self.remove_roles)

        content = self._content

        return (
            f"- _{self._prefix}{' ' if content else ''} {f'**{content}**' if content else ''}{' ' if content else ''}receive the "
            f"role{'s' if len(self.roles) > 1  else ''} {role_mentions}"
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

async def get_binds(guild_id: int | str, category: VALID_BIND_TYPES = None, bind_id: int = None) -> list[GuildBind]:
    """Get the current guild binds.

    Old binds will be included by default, but will not be saved in the database in the
    new format unless the POP_OLD_BINDS flag is set to True. While it is False, old formatted binds will
    be left as is.
    """

    guild_id = str(guild_id)
    guild_data = await database.fetch_guild_data(guild_id, "binds")

    return list(filter(lambda b: b.type == category and ((bind_id and b.criteria.id == bind_id) or not bind_id), guild_data.binds) if category else guild_data.binds)

    # Convert and save old bindings in the new format
    # if not guild_data.converted_binds and (
    #     guild_data.groupIDs is not None or guild_data.roleBinds is not None
    # ):
    #     old_binds = []

    #     if guild_data.groupIDs:
    #         old_binds.extend(convert_v3_binds_to_v4(guild_data.groupIDs, "group"))

    #     if guild_data.roleBinds:
    #         gamepasses = guild_data.roleBinds.get("gamePasses")
    #         if gamepasses:
    #             old_binds.extend(convert_v3_binds_to_v4(gamepasses, "gamepass"))

    #         assets = guild_data.roleBinds.get("assets")
    #         if assets:
    #             old_binds.extend(convert_v3_binds_to_v4(assets, "asset"))

    #         badges = guild_data.roleBinds.get("badges")
    #         if badges:
    #             old_binds.extend(convert_v3_binds_to_v4(badges, "badge"))

    #         group_ranks = guild_data.roleBinds.get("groups")
    #         if group_ranks:
    #             old_binds.extend(convert_v3_binds_to_v4(group_ranks, "group"))

    #     if old_binds:
    #         # Prevent duplicates from being made. Can't use sets because dicts aren't hashable
    #         guild_data.binds.extend(bind for bind in old_binds if bind not in guild_data.binds)

    #         await update_guild_data(guild_id, binds=guild_data.binds, converted_binds=True)
    #         guild_data.converted_binds = True

    # if POP_OLD_BINDS and guild_data.converted_binds:
    #     await update_guild_data(guild_id, groupIDs=None, roleBinds=None, converted_binds=None)

    # return [
    #     GuildBind(**bind) for bind in guild_data.binds
    # ]


# def convert_v3_binds_to_v4(items: dict, bind_type: str) -> list:
#     """Convert old bindings to the new bind format.

#     Args:
#         items (dict): The bindings to convert.
#         bind_type (ValidBindType): Type of bind that is being made.

#     Returns:
#         list: The binds in the new format.
#     """
#     output = []

#     for bind_id, data in items.items():
#         group_rank_binding = data.get("binds") or data.get("ranges")

#         if bind_type != "group" or not group_rank_binding:
#             bind_data = {
#                 "roles": data.get("roles"),
#                 "removeRoles": data.get("removeRoles"),
#                 "nickname": data.get("nickname"),
#                 "bind": {"type": bind_type, "id": int(bind_id)},
#             }
#             output.append(bind_data)
#             continue

#         # group rank bindings
#         if data.get("binds"):
#             for rank_id, sub_data in data["binds"].items():
#                 bind_data = {}

#                 bind_data["bind"] = {"type": bind_type, "id": int(bind_id)}
#                 bind_data["roles"] = sub_data.get("roles")
#                 bind_data["nickname"] = sub_data.get("nickname")
#                 bind_data["removeRoles"] = sub_data.get("removeRoles")

#                 # Convert to an int if possible beforehand.
#                 try:
#                     rank_id = int(rank_id)
#                 except ValueError:
#                     pass

#                 if rank_id == "all":
#                     bind_data["bind"]["everyone"] = True
#                 elif rank_id == 0:
#                     bind_data["bind"]["guest"] = True
#                 elif rank_id < 0:
#                     bind_data["bind"]["min"] = abs(rank_id)
#                 else:
#                     bind_data["bind"]["roleset"] = rank_id

#                 output.append(bind_data)

#         # group rank ranges
#         if data.get("ranges"):
#             for range_item in data["ranges"]:
#                 bind_data = {}

#                 bind_data["bind"] = {"type": bind_type, "id": int(bind_id)}
#                 bind_data["roles"] = range_item.get("roles")
#                 bind_data["nickname"] = range_item.get("nickname")
#                 bind_data["removeRoles"] = range_item.get("removeRoles")

#                 bind_data["bind"]["min"] = int(range_item.get("low"))
#                 bind_data["bind"]["max"] = int(range_item.get("high"))

#                 output.append(bind_data)

#     return output


# def json_binds_to_guild_binds(bind_list: list) -> list:
#     """Convert a bind from a dict/json representation to a GuildBind or GroupBind object.

#     Args:
#         bind_list (list): List of bindings to convert
#         category (ValidBindType, optional): Category to filter the binds by. Defaults to None.
#         id_filter (str, optional): ID to filter the binds by. Defaults to None.
#             Applied after the category if both are given.

#     Raises:
#         BloxlinkException: When no matching bind type is found from the json input.

#     Returns:
#         list: The list of bindings as GroupBinds or GuildBinds, filtered by the category & id.
#     """
#     binds = []

#     for bind in bind_list:
#         bind_data = bind.get("bind")
#         bind_type = bind_data.get("type")

#         if bind_type == "group":
#             classed_bind = GroupBind(**bind)
#         elif bind_type:
#             classed_bind = GuildBind(**bind)
#         else:
#             raise BloxlinkException("Invalid bind structure found.")

#         binds.append(classed_bind)

#     binds.sort(key=lambda e: e.bind["id"])
#     return binds
