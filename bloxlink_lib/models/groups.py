from __future__ import annotations

import re
from attrs import define, field
from typing import TYPE_CHECKING
from ..fetch import fetch, fetch_typed
from ..exceptions import RobloxAPIError, RobloxNotFound

from .base import RobloxEntity

if TYPE_CHECKING:
    from .users import RobloxUser

GROUP_API = "https://groups.roblox.com/v1/groups"
ROBLOX_GROUP_REGEX = re.compile(r"roblox.com/groups/(\d+)/")


@define(slots=True, kw_only=True)
class GroupRoleset:
    """Representation of a roleset in a Roblox group."""

    name: str
    rank: int # User-assigned rank ID
    id: int # Roblox-assigned roleset ID
    memberCount: int = field(alias="member_count", default=None)

@define(slots=True, kw_only=True)
class RobloxRolesetResponse:
    """Representation of the response from the Roblox roleset API."""

    groupId: int
    roles: list[GroupRoleset]

@define(slots=True, kw_only=True)
class RobloxGroupOwnerResponse:
    """Representation of a group owner in a Roblox group."""

    userId: int
    username: str
    displayName: str
    hasVerifiedBadge: bool

@define(slots=True, kw_only=True)
class RobloxGroupResponse:
    """Representation of the response from the Roblox group API."""

    id: int
    name: str
    description: str
    memberCount: int
    owner: RobloxGroupOwnerResponse
    shout: str | None
    publicEntryAllowed: bool
    hasVerifiedBadge: bool


@define(kw_only=True, slots=True)
class RobloxGroup(RobloxEntity):
    """Representation of a Group on Roblox.


    Attributes:
        member_count (int): Number of members in this group. None by default.
        rolesets (dict[int, str], optional): Rolesets of this group, by {roleset_id: roleset_name}. None by default.
        user_roleset (dict): The roleset of a specific user in this group. Used for applying binds.

    This is in addition to attributes provided by RobloxEntity.
    """

    member_count: int = None
    rolesets: dict[int, GroupRoleset] = None
    user_roleset: GroupRoleset = None

    def __attrs_post_init__(self):
        self.url = f"https://www.roblox.com/groups/{self.id}"

    async def sync(self):
        """Retrieve the roblox group information, consisting of rolesets, name, description, and member count."""
        if self.synced:
            return

        if self.rolesets is None:
            roleset_data, _ = await fetch_typed(f"{GROUP_API}/{self.id}/roles", RobloxRolesetResponse)
            self.rolesets = {int(roleset.rank): GroupRoleset(**roleset) for roleset in roleset_data.roles}

        group_data, _ = await fetch_typed(f"{GROUP_API}/{self.id}", RobloxGroupResponse)

        self.name = group_data.name
        self.description = group_data.description
        self.member_count = group_data.memberCount

        self.synced = True

    async def sync_for(self, roblox_user: RobloxUser):
        """Sync and retrieve the roleset of a specific user in this group."""

        await self.sync()

        if self.user_roleset is None:
            await roblox_user.sync(sync_groups=False)
            print(roblox_user.groups)

            user_group = roblox_user.groups.get(self.id)

            if user_group:
                self.user_roleset = user_group.user_roleset


    def __str__(self) -> str:
        name = f"**{self.name}**" if self.name else "*(Unknown Group)*"
        return f"{name} ({self.id})"

    def roleset_name_string(self, roleset_id: int, bold_name=True, include_id=True) -> str:
        """Generate a nice string for a roleset name with failsafe capabilities.

        Args:
            roleset_id (int): ID of the Roblox roleset.
            bold_name (bool, optional): Wraps the name in ** when True. Defaults to True.
            include_id (bool, optional): Includes the ID in parenthesis when True. Defaults to True.

        Returns:
            str: The roleset string as requested.
        """
        roleset_name = self.rolesets.get(roleset_id, "")
        if not roleset_name:
            return str(roleset_id)

        if bold_name:
            roleset_name = f"**{roleset_name}**"

        return f"{roleset_name} ({roleset_id})" if include_id else roleset_name


async def get_group(group_id_or_url: str | int) -> RobloxGroup:
    """Get and sync a RobloxGroup.

    Args:
        group_id_or_url (str): ID or URL of the group to retrieve

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

    group: RobloxGroup = RobloxGroup(id=group_id)

    try:
        await group.sync()  # this will raise if the group doesn't exist
    except RobloxAPIError as exc:
        raise RobloxNotFound("This group does not exist.") from exc

    return group
