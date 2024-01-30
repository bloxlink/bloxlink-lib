from attrs import define, fields
from typing import Literal
from datetime import datetime
from abc import ABC, abstractmethod


@define(slots=True, kw_only=True)
class BaseModel: # pylint: disable=too-many-instance-attributes
    """Base representation of a model."""

    def to_dict(self) -> dict[str | int, str | int]:
        """Convert the object into a dict of values."""

        for field in fields(self.__class__):
            match getattr(self, field.name):
                case datetime():
                    setattr(self, field.name, getattr(self, field.name).isoformat())

        return {field.name: getattr(self, field.name) for field in fields(self.__class__)}


@define(slots=True)
class RobloxEntity(ABC):
    """Representation of an entity on Roblox.

    Attributes:
        id (str, optional): Roblox given ID of the entity.
        name (str, optional): Name of the entity.
        description (str, optional): The description of the entity (if any).
        synced (bool): If this entity has been synced with Roblox or not. False by default.
    """

    id: str
    name: str = None
    description: str = None
    synced: bool = False
    url: str = None

    @abstractmethod
    async def sync(self):
        """Sync a Roblox entity with the data from Roblox."""
        raise NotImplementedError()

    def __str__(self) -> str:
        name = f"**{self.name}**" if self.name else "*(Unknown Roblox Entity)*"
        return f"{name} ({self.id})"


def create_entity(
    category: Literal["asset", "badge", "gamepass", "group"] | str, entity_id: int
) -> RobloxEntity:
    """Create a respective Roblox entity from a category and ID.

    Args:
        category (str): Type of Roblox entity to make. Subset from asset, badge, group, gamepass.
        entity_id (int): ID of the entity on Roblox.

    Returns:
        RobloxEntity: The respective RobloxEntity implementer, unsynced.
    """
    match category:
        case "asset":
            # from resources.api.roblox.assets import RobloxAsset  # pylint: disable=import-outside-toplevel

            # return RobloxAsset(entity_id)
            raise NotImplementedError()

        case "badge":
            # from resources.api.roblox.badges import RobloxBadge  # pylint: disable=import-outside-toplevel

            # return RobloxBadge(entity_id)
            raise NotImplementedError()

        case "gamepass":
            # from resources.api.roblox.gamepasses import RobloxGamepass  # pylint: disable=import-outside-toplevel

            # return RobloxGamepass(entity_id)
            raise NotImplementedError()

        case "group":
            from .groups import RobloxGroup  # pylint: disable=import-outside-toplevel

            return RobloxGroup(entity_id)
