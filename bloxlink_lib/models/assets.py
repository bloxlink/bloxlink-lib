from pydantic import Field
from ..fetch import fetch_typed
from .base import BaseModel, get_entity
from .base_assets import RobloxBaseAsset


ASSET_API = "https://economy.roblox.com/v2/assets"


class RobloxAssetResponse(BaseModel):
    """Representation of the response from the Roblox Asset API."""

    id: int = Field(alias="AssetId")
    name: str = Field(alias="Name")
    description: str = Field(alias="Description")


class RobloxAsset(RobloxBaseAsset):
    """Representation of a catalog asset on Roblox."""

    type: str = "asset"

    async def sync(self):
        """Load catalog asset data from Roblox"""

        if self.synced:
            return

        asset_data, _ = await fetch_typed(RobloxAssetResponse, f"{ASSET_API}/{self.id}/details")

        self.name = asset_data.name
        self.description = asset_data.description

        self.synced = True


async def get_catalog_asset(asset_id: int) -> RobloxAsset:
    """Wrapper around get_entity() to get and sync a catalog asset from Roblox.

    Args:
        asset_id (int): ID of the catalog asset.

    Returns:
        RobloxAsset: A synced Roblox catalog asset.
    """

    return await get_entity("asset", asset_id)
