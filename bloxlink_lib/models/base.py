from typing import Literal, Annotated, Tuple, Type, Iterable, Any, get_args, Self, Callable
from abc import ABC, abstractmethod
from pydantic import BaseModel as PydanticBaseModel, BeforeValidator, WithJsonSchema, ConfigDict
from pydantic.fields import FieldInfo

Snowflake = Annotated[int, BeforeValidator(
    int), WithJsonSchema({"type": 'int'})]


class UNDEFINED:
    """
    Can be used to differentiate between None and undefined
    in function arguments.
    """


class BaseModelArbitraryTypes(PydanticBaseModel):
    """Base model with arbitrary types allowed."""

    model_config = ConfigDict(arbitrary_types_allowed=True,
                              populate_by_name=True, validate_assignment=True)


class BaseModel(PydanticBaseModel):
    """Base model with a set configuration."""

    model_config = ConfigDict(populate_by_name=True, validate_assignment=True)

    @classmethod
    def model_fields_index(cls: Type[PydanticBaseModel | BaseModelArbitraryTypes]) -> list[Tuple[str, FieldInfo]]:
        """Returns a list of the model's fields with the name as a tuple.

        Useful if the field index is necessary.

        """

        fields_with_names: list[Tuple[str, FieldInfo]] = []

        for field_name, field in cls.model_fields.items():
            fields_with_names.append((field_name, field))

        return fields_with_names


class RobloxEntity(BaseModel, ABC):
    """Representation of an entity on Roblox.

    Attributes:
        id (str): Roblox given ID of the entity.
        name (str, optional): Name of the entity.
        description (str, optional): The description of the entity (if any).
        synced (bool): If this entity has been synced with Roblox or not. False by default.
    """

    id: int | None
    name: str = None
    description: str | None = None
    synced: bool = False
    url: str = None

    @abstractmethod
    async def sync(self):
        """Sync a Roblox entity with the data from Roblox."""
        raise NotImplementedError()

    def __str__(self) -> str:
        name = f"**{self.name}**" if self.name else "*(Unknown Roblox Entity)*"
        return f"{name} ({self.id})"


class BloxlinkEntity(RobloxEntity):
    """Entity for Bloxlink-specific operations."""

    type: Literal["verified", "unverified"]
    id: None = None

    async def sync(self):
        pass

    def __str__(self) -> str:
        return "Verified Users" if self.type == "verified" else "Unverified Users"


class CoerciveSet[T: Callable](set[T]):
    """A set that coerces the children into another type."""

    def __init__(self, *s: Iterable[T]):
        super().__init__(self._coerce(x) for i in s for x in i)

    def _coerce(self, item: Any) -> T:
        try:
            target_type = get_args(self.__orig_bases__[0])[0]
        except (IndexError, AttributeError):
            raise TypeError("Cannot determine the target type for coercion")

        if isinstance(item, target_type):
            return item
        try:
            return target_type(item)
        except (TypeError, ValueError):
            raise TypeError(f"Cannot coerce {item} to {target_type}")

    def __contains__(self, item):
        return super().__contains__(self._coerce(item))

    def add(self, item):
        return super().add(self._coerce(item))

    def remove(self, item):
        return super().remove(self._coerce(item))

    def discard(self, item):
        return super().discard(self._coerce(item))

    def update(self, *s: Iterable[T]):
        return super().update(set(self._coerce(x) for i in s for x in i))

    def intersection(self, *s: Iterable[T]):
        return super().intersection(set(self._coerce(x) for i in s for x in i))

    def difference(self, *s: Iterable[T]):
        return super().difference(set(self._coerce(x) for i in s for x in i))

    def symmetric_difference(self, *s: Iterable[T]):
        return super().symmetric_difference(set(self._coerce(x) for i in s for x in i))

    def union(self, *s: Iterable[T]) -> Self:
        return super().union(set(self._coerce(x) for iterable in s for x in iterable))

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v: Any, field: Any) -> 'CoerciveSet[T]':
        if not isinstance(v, (set, list, tuple)):
            raise TypeError(f'Invalid type for CoerciveSet: {type(v)}')

        return cls(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, schema: dict) -> dict:
        schema.update(
            type='array',
            items={'type': 'string'},
        )
        return schema

    def __json__(self):
        return list(self)

    def __repr__(self):
        return f"{self.__class__.__name__}({super().__repr__()})"


class SnowflakeSet(CoerciveSet[int]):
    """A set of Snowflakes."""

    def __init__(self, *s: Iterable[int], type: Literal["role", "user"] = None, str_reference: dict = None):
        super().__init__(*s)
        self.type = type
        self.str_reference = str_reference or {}

    def add(self, item):
        """Add an item to the set. If the item contains an ID, it will be parsed into an integer. Otherwise, it will be added as an int."""

        if getattr(item, "id", None):
            return super().add(item.id)

        return super().add(item)

    def __str__(self):
        match self.type:
            case "role":
                return ", ".join(str(self.str_reference.get(i) or f"<@&{i}>") for i in self)

            case "user":
                return ", ".join(str(self.str_reference.get(i) or f"<@{i}>") for i in self)

        return ", ".join(str(self.str_reference.get(i) or i) for i in self)

    def __repr__(self):
        return f"{self.__class__.__name__}({super().__repr__()})"


def create_entity(
    category: Literal["asset", "badge", "gamepass", "group", "verified", "unverified"] | str, entity_id: int
) -> RobloxEntity | None:
    """Create a respective Roblox entity from a category and ID.

    Args:
        category (str): Type of Roblox entity to make. Subset from asset, badge, group, gamepass.
        entity_id (int): ID of the entity on Roblox.

    Returns:
        RobloxEntity: The respective RobloxEntity implementer, unsynced, or None if the category is invalid.
    """

    match category:
        case "asset":
            from bloxlink_lib.models import assets  # pylint: disable=import-outside-toplevel

            return assets.RobloxAsset(id=entity_id)

        case "badge":
            from bloxlink_lib.models import badges  # pylint: disable=import-outside-toplevel

            return badges.RobloxBadge(id=entity_id)

        case "gamepass":
            from bloxlink_lib.models import gamepasses  # pylint: disable=import-outside-toplevel

            return gamepasses.RobloxGamepass(id=entity_id)

        case "group":
            from bloxlink_lib.models import groups  # pylint: disable=import-outside-toplevel

            return groups.RobloxGroup(id=entity_id)

        case "verified" | "unverified":
            return BloxlinkEntity(type=category)

    return None


async def get_entity(
    category: Literal["asset", "badge", "gamepass", "group"] | str, entity_id: int
) -> RobloxEntity:
    """Get and sync a Roblox entity.

    Args:
        category (str): Type of Roblox entity to get. Subset from asset, badge, group, gamepass.
        entity_id (int): ID of the entity on Roblox.

    Returns:
        RobloxEntity: The respective RobloxEntity implementer, synced.
    """

    entity = create_entity(category, int(entity_id))

    await entity.sync()

    return entity
