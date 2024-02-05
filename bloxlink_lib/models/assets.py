from typing import Literal
# import bloxlink_lib.models.badges as badges
from ..exceptions import RobloxAPIError, RobloxNotFound

from .base import RobloxEntity


# ASSET_API = "https://economy.roblox.com/v2/assets"


class RobloxAsset(RobloxEntity):
    """
    Representation of an Asset on Roblox.
    This includes catalog assets, badges, gamepasses, and bundles.
    """

    type: Literal["asset", "badge", "gamepass", "bundle"] = None
    type_number: int = None


    def __str__(self) -> str:
        name = f"**{self.name}**" if self.name else f"*(Unknown {self.type.capitalize()})*"

        return f"{name} ({self.id})"


# async def get_asset(asset_id: int, type: Literal["asset", "badge", "gamepass", "bundle"]) -> RobloxAsset:
#     """Get and sync an asset from Roblox.

#     Args:
#         asset_id (str): ID of the asset.
#         type (str): Type of the asset. Subset from asset, badge, gamepass, bundle.

#     Raises:
#         RobloxNotFound: Raises RobloxNotFound when the Roblox API has an error.

#     Returns:
#         RobloxAsset: A synced roblox asset.
#     """

#     match type:
#         case "catalogAsset":
#             raise NotImplementedError()
#         case "badge":
#             asset = badges.RobloxBadge(id=asset_id)
#         case "gamepass":
#             raise NotImplementedError()
#         case "bundle":
#             raise NotImplementedError()
#         case _:
#             raise ValueError("Invalid asset type.")

#     try:
#         await asset.sync()  # this will raise if the asset doesn't exist
#     except RobloxAPIError as exc:
#         raise RobloxNotFound("This asset does not exist.") from exc

#     return asset
