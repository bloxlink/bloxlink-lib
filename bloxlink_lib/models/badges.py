import bloxlink_lib.models.assets as assets
from ..fetch import fetch_typed
from .base import BaseModel



BADGE_API = "https://badges.roblox.com/v1/badges"


class RobloxBadgeResponse(BaseModel):
    """Representation of the response from the Roblox badge API."""

    id: int
    name: str
    description: str


class RobloxBadge(assets.RobloxAsset):
    """Representation of a Badge on Roblox."""

    type: str = "badge"
    type_number: int = 2

    async def sync(self):
        """Load badge data from Roblox"""

        if self.synced:
            return

        badge_data, _ = await fetch_typed(f"{BADGE_API}/{self.id}", RobloxBadgeResponse)

        self.name = badge_data.name
        self.description = badge_data.description

        self.synced = True


# async def get_badge(badge_id: int) -> RobloxBadge:
#     """Wrapper around get_asset() to get and sync a badge from Roblox.

#     Args:
#         badge_id (int): ID of the badge.

#     Returns:
#         RobloxBadge: A synced roblox badge.
#     """

#     return await assets.get_asset(badge_id, "badge")
