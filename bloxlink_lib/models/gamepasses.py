from pydantic import Field
from ..fetch import fetch_typed
from .base import BaseModel, get_entity
from .assets import RobloxAsset



GAMEPASS_API = "https://economy.roblox.com/v1/game-pass"


class RobloxGamepassResponse(BaseModel):
    """Representation of the response from the Roblox Gamepass API."""

    id: int
    name: str = Field(alias="Name")
    description: str = Field(alias="Description")


class RobloxGamepass(RobloxAsset):
    """Representation of a Gamepass on Roblox."""

    type: str = "gamepass"

    async def sync(self):
        """Load Gamepass data from Roblox"""

        if self.synced:
            return

        gamepass_data, _ = await fetch_typed(f"{GAMEPASS_API}/{self.id}/game-pass-product-info", RobloxGamepassResponse)

        self.name = gamepass_data.name
        self.description = gamepass_data.description

        self.synced = True


async def get_gamepass(gamepass_id: int) -> RobloxGamepass:
    """Wrapper around get_entity() to get and sync a gamepass from Roblox.

    Args:
        gamepass_id (int): ID of the Gamepass.

    Returns:
        RobloxGamepass: A synced Roblox Gamepass.
    """

    return await get_entity("gamepass", gamepass_id)
