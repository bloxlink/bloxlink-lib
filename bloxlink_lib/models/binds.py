from __future__ import annotations
from typing import Literal, TYPE_CHECKING

from pydantic import BaseModel, Field

from ..models.base import RobloxEntity, create_entity
import bloxlink_lib.database as database

if TYPE_CHECKING:
    from .guilds import RoleSerializable
    from .users import MemberSerializable, RobloxUser
    from .groups import RobloxGroup

POP_OLD_BINDS: bool = False

VALID_BIND_TYPES = Literal["group", "asset", "badge", "gamepass", "verified", "unverified"]


class GroupBindData(BaseModel):
    """Represents the data required for a group bind."""

    everyone: bool
    guest: bool
    min: int = None
    max: int = None
    roleset: int = None

class BindCriteria(BaseModel):
    """Represents the criteria required for a bind. If anything is set, it must ALL be met."""

    type: VALID_BIND_TYPES
    id: int = None

    group: GroupBindData = None
    # asset
    # badge
    # gamepass


# class BindToDict(BaseModel):
#     """Represents the top level of a bind."""

#     nickname: str
#     roles: list
#     removeRoles: list

#     criteria: BindCriteria


class GuildBind(BaseModel):
    """Represents a role binding from the database.

    Attributes:
        nickname (str, optional): The nickname template to be applied to users. Defaults to None.
        roles (list): The IDs of roles that should be given by this bind.
        removeRole (list): The IDs of roles that should be removed when this bind is given.

        criteria (BindCriteria): Bind-specific requirements

        entity (RobloxEntity, optional): The entity that this binding represents. Defaults to None.
    """

    nickname: str = None
    roles: list[str] = Field(default_factory=list)
    remove_roles: list[str] = Field(default_factory=list, alias="removeRoles")

    criteria: BindCriteria
    entity: RobloxEntity = Field(exclude=True, default=None)
    type: Literal["group", "asset", "badge", "gamepass", "verified", "unverified"] | None = Field(exclude=True, default=None)
    subtype: Literal["linked_group", "full_group"] | None = Field(exclude=True, default=None)

    def model_post_init(self, __context):
        self.entity = self.entity or create_entity(self.criteria["type"], self.criteria["id"])
        self.type = self.criteria.type

        if self.type == "group":
            self.subtype = "linked_group" if (self.criteria.group.roleset or (self.criteria.group.min and self.criteria.group.max)) else "full_group"

    async def satisfies_for(self, guild_roles: dict[str, RoleSerializable], member: MemberSerializable, roblox_user: RobloxUser | None = None) -> tuple[bool, list[RoleSerializable]]:
        """Check if a user satisfies the requirements for this bind."""

        ineligible_roles: list[str] = []

        if not roblox_user:
            if self.criteria.type == "unverified":
                return True, ineligible_roles

            # user is unverified, so remove Verified role
            if self.criteria.type == "verified":
                for role_id in filter(lambda r: int(r) in member.role_ids, self.roles):
                    ineligible_roles.append(str(guild_roles[role_id].id))

            return False, ineligible_roles


        # user is verified
        await roblox_user.sync()

        match self.criteria.type:
            case "verified":
                return True, ineligible_roles

            case "group":
                if self.criteria.id in roblox_user.groups:
                    if self.criteria.group.everyone:
                        return True, ineligible_roles

                    if self.criteria.group.guest:
                        return False, ineligible_roles

                    group: RobloxGroup = self.entity

                    await group.sync_for(roblox_user)

                    print(group)

                    if (self.criteria.group.min and self.criteria.group.max) and (self.criteria.group.min <= group.user_roleset.rank <= self.criteria.group.max):
                        return True, ineligible_roles

                    if self.criteria.group.roleset:
                        return group.user_roleset.rank == self.criteria.group.roleset, ineligible_roles



                    return True, ineligible_roles

                # Not in group. Return whether the bind is for guests only
                return self.criteria.group.guest, ineligible_roles



        return False


async def get_binds(guild_id: int | str, category: VALID_BIND_TYPES = None) -> list[GuildBind]:
    """Get the current guild binds.

    Old binds will be included by default, but will not be saved in the database in the
    new format unless the POP_OLD_BINDS flag is set to True. While it is False, old formatted binds will
    be left as is.
    """

    guild_id = str(guild_id)
    guild_data = await database.fetch_guild_data(guild_id, "binds")

    return list(filter([b for b in guild_data.binds if b.type == category] if category else guild_data.binds))

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
