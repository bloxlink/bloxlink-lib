from __future__ import annotations

import re
from typing import TYPE_CHECKING, Annotated
from pydantic import Field
from ..fetch import fetch_typed
from ..exceptions import RobloxAPIError, RobloxNotFound

from .base import RobloxEntity, BaseModel

if TYPE_CHECKING:
    from .users import RobloxUser

GROUP_API = "https://groups.roblox.com/v1/groups"
ROBLOX_GROUP_REGEX = re.compile(r"roblox.com/groups/(\d+)/")


class GroupRoleset(BaseModel):
    """Representation of a roleset in a Roblox group."""

    name: str
    rank: int # User-assigned rank ID
    id: int # Roblox-assigned roleset ID
    member_count: int | None = Field(alias="memberCount", default=None)


class RobloxRoleset(BaseModel):
    """Representation of the response from the Roblox roleset API."""

    group_id: int = Field(alias="groupId")
    roles: list[GroupRoleset]


class RobloxGroupOwner(BaseModel):
    """Representation of a group owner in a Roblox group."""

    user_id: int = Field(alias="userId")
    username: str
    display_name: str = Field(alias="displayName")
    has_verified_badge: bool = Field(alias="hasVerifiedBadge")


class RobloxGroupResponse(BaseModel):
    """Representation of the response from the Roblox group API."""

    id: int
    name: str
    description: str
    member_count: int = Field(alias="memberCount")
    owner: RobloxGroupOwner
    shout: str | None
    public_entry_allowed: bool = Field(alias="publicEntryAllowed")
    has_verified_badge: bool = Field(alias="hasVerifiedBadge")


class RobloxGroup(RobloxEntity):
    """Representation of a Group on Roblox.


    Attributes:
        member_count (int): Number of members in this group. None by default.
        rolesets (dict[int, str], optional): Rolesets of this group, by {roleset_id: roleset_name}. None by default.
        user_roleset (dict): The roleset of a specific user in this group. Used for applying binds.

    This is in addition to attributes provided by RobloxEntity.
    """

    member_count: int = Field(alias="memberCount", default=None)
    rolesets: dict[int, GroupRoleset] = None
    user_roleset: GroupRoleset = None
    shout: str = Field(default=None)
    has_verified_badge: bool = Field(alias="hasVerifiedBadge", default=None)
    owner: RobloxGroupOwner = None
    public_entry_allowed: bool = Field(alias="publicEntryAllowed", default=None)
    has_verified_badge: bool = Field(alias="hasVerifiedBadge", default=None)

    def model_post_init(self, __context):
        self.url = f"https://www.roblox.com/groups/{self.id}"

    async def sync(self):
        """Retrieve the roblox group information, consisting of rolesets, name, description, and member count."""
        if self.synced:
            return

        if self.rolesets is None:
            roleset_data, _ = await fetch_typed(f"{GROUP_API}/{self.id}/roles", RobloxRoleset)
            self.rolesets = {int(roleset.rank): GroupRoleset(**roleset) for roleset in roleset_data.roles}

        group_data, _ = await fetch_typed(f"{GROUP_API}/{self.id}", RobloxGroup)

        self.name = group_data.name
        self.description = group_data.description
        self.member_count = group_data.member_count

        self.synced = True

    async def sync_for(self, roblox_user: RobloxUser, sync: bool = False):
        """Sync and retrieve the roleset of a specific user in this group."""

        if sync:
            await self.sync()

        if self.user_roleset is None:
            if roblox_user.groups is None:
                await roblox_user.sync(["groups"])

            user_group = roblox_user.groups.get(self.id)

            if user_group:
                self.user_roleset = user_group.role

    def roleset_name_string(self, roleset_id: int, bold_name=True, include_id=True) -> str:
        """Generate a nice string for a roleset name with failsafe capabilities.

        Args:
            roleset_id (int): ID of the Roblox roleset.
            bold_name (bool, optional): Wraps the name in ** when True. Defaults to True.
            include_id (bool, optional): Includes the ID in parenthesis when True. Defaults to True.

        Returns:
            str: The roleset string as requested.
        """

        roleset_name = self.rolesets.get(roleset_id).name if self.rolesets else str(roleset_id)

        if bold_name:
            roleset_name = f"**{roleset_name}**"

        return f"{roleset_name} ({roleset_id})" if include_id else roleset_name


    def __str__(self) -> str:
        name = f"**{self.name}**" if self.name else "*(Unknown Group)*"
        return f"{name} ({self.id})"


async def get_group(group_id_or_url: Annotated[str | int, "Group ID or URL"]) -> RobloxGroup:
    """Get and sync a RobloxGroup.

    Args:
        group_id_or_url (str | int): ID or URL of the group to retrieve

    Raises:
        RobloxNotFound: Raises RobloxNotFound when the Roblox API has an error.

    Returns:
        RobloxGroup: A synced roblox group.
    """

    group_id_or_url = str(group_id_or_url)
    regex_search = ROBLOX_GROUP_REGEX.search(group_id_or_url)

    if regex_search:
        group_id = regex_search.group(1)
    else:
        group_id = group_id_or_url

    group = RobloxGroup(id=group_id)

    try:
        await group.sync()  # this will raise if the group doesn't exist
    except RobloxAPIError as exc:
        raise RobloxNotFound("This group does not exist.") from exc

    return group
