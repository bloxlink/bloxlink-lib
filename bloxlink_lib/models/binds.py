from typing import Literal, TypedDict, NotRequired
from attrs import define, field, asdict

from ..database import fetch_guild_data
from ..models.base import BaseModel
from .guilds import GuildData

POP_OLD_BINDS: bool = False

VALID_BINDS = Literal["group", "asset", "badge", "gamepass", "verified", "unverified"]


class GroupBindData(TypedDict):
    """Represents the data required for a group bind."""

    min: NotRequired[int]
    max: NotRequired[int]
    roleset: NotRequired[int]
    everyone: bool
    guest: bool

class BindData(TypedDict):
    """Represents the data required for a bind."""

    type: VALID_BINDS
    id: NotRequired[int]

    group: GroupBindData

class BindToDict(TypedDict):
    """Represents the top level of a bind."""

    nickname: str
    roles: list
    removeRoles: list

    bind: BindData

@define(slots=True, kw_only=True)
class GuildBind(BaseModel):
    """Represents a role binding from the database.

    Attributes:
        nickname (str, optional): The nickname template to be applied to users. Defaults to None.
        roles (list): The IDs of roles that should be given by this bind.
        removeRole (list): The IDs of roles that should be removed when this bind is given.

        bind (BindToDict): Bind-specific requirements

        entity (RobloxEntity, optional): The entity that this binding represents. Defaults to None.
    """

    nickname: str = None
    roles: list = field(factory=list)
    removeRoles: list = field(factory=list)

    bind: BindData

    def to_dict(self) -> BindToDict:
        return asdict(self)


async def get_binds(guild_id: int | str) -> list[GuildBind]:
    """Get the current guild binds.

    Old binds will be included by default, but will not be saved in the database in the
    new format unless the POP_OLD_BINDS flag is set to True. While it is False, old formatted binds will
    be left as is.
    """

    guild_id = str(guild_id)
    guild_data: GuildData = await fetch_guild_data(
        guild_id, "binds", "groupIDs", "roleBinds", "converted_binds"
    )

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

    return [
        GuildBind(**bind) for bind in guild_data.binds
    ]


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
