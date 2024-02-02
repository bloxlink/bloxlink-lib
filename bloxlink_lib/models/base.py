from typing import Literal, Annotated
from abc import ABC, abstractmethod
from pydantic import BaseModel as PydanticBaseModel, BeforeValidator, WithJsonSchema



Snowflake = Annotated[int, BeforeValidator(int), WithJsonSchema({"type": 'int'})]


class BaseModelConfig:
    """Configuration for a base model."""

    populate_by_name = True

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class BaseModelArbitraryTypes(PydanticBaseModel):
    """Base model with arbitrary types allowed."""

    Config = BaseModelConfig(arbitrary_types_allowed=True)


class BaseModel(PydanticBaseModel):
    """Base model with a set configuration."""

    Config = BaseModelConfig()


class RobloxEntity(BaseModel, ABC):
    """Representation of an entity on Roblox.

    Attributes:
        id (str): Roblox given ID of the entity.
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

            # return RobloxAsset(id=entity_id)
            raise NotImplementedError()

        case "badge":
            # from resources.api.roblox.badges import RobloxBadge  # pylint: disable=import-outside-toplevel

            # return RobloxBadge(id=entity_id)
            raise NotImplementedError()

        case "gamepass":
            # from resources.api.roblox.gamepasses import RobloxGamepass  # pylint: disable=import-outside-toplevel

            # return RobloxGamepass(id=entity_id)
            raise NotImplementedError()

        case "group":
            from .groups import RobloxGroup  # pylint: disable=import-outside-toplevel

            return RobloxGroup(id=entity_id)
