from pydantic import Field
from ..fetch import fetch_typed
from .base import BaseModel, get_entity
from .assets import RobloxAsset



ASSET_API = "https://economy.roblox.com/v2/assets"


class RobloxCatalogAssetResponse(BaseModel):
    """Representation of the response from the Roblox Asset API."""

    id: int
    name: str = Field(alias="Name")
    description: str = Field(alias="Description")


class RobloxCatalogAsset(RobloxAsset):
    """Representation of a catalog asset on Roblox."""

    type: str = "catalogAsset"

    async def sync(self):
        """Load catalog asset data from Roblox"""

        if self.synced:
            return

        asset_data, _ = await fetch_typed(f"{ASSET_API}/{self.id}/details", RobloxCatalogAssetResponse)

        self.name = asset_data.name
        self.description = asset_data.description

        self.synced = True


async def get_catalog_asset(asset_id: int) -> RobloxCatalogAsset:
    """Wrapper around get_entity() to get and sync a catalog asset from Roblox.

    Args:
        asset_id (int): ID of the catalog asset.

    Returns:
        RobloxCatalogAsset: A synced Roblox catalog asset.
    """

    return await get_entity("catalogAsset", asset_id)
