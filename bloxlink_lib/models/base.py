from pydantic import BaseModel, PrivateAttr
from typing import Callable, Iterable, Type, Any, get_args, Callable, Sequence, Annotated, Literal, Tuple, Set
from abc import ABC, abstractmethod
from pydantic import BaseModel as PydanticBaseModel, BeforeValidator, WithJsonSchema, ConfigDict, Field, ConfigDict
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


class CoerciveSet[T: Callable](BaseModel):
    """A set that coerces the children into another type."""

    root: Sequence[T] | Set[T]
    data: set[T] = Field(default_factory=set)
    _target_type: Type[T] | None = PrivateAttr(default=None)

    def __init__(self, **data):
        print(data)
        super().__init__(
            root=data.get("root", []),
        )

    def model_post_init(self, __context: Any) -> None:
        self.data = set(self._coerce(x) for x in self.root)

    def _get_type(self) -> Type[T]:
        if self._target_type:
            return self._target_type

        try:
            target_type = get_args(self.__annotations__['data'])[0]
            self._target_type = target_type
        except (IndexError, AttributeError):
            raise TypeError("Cannot determine the target type for coercion")
        else:
            return target_type

    def _coerce(self, item: Any) -> T:
        target_type = self._get_type()

        if isinstance(item, target_type):
            return item
        try:
            return target_type(item)
        except (TypeError, ValueError):
            raise TypeError(f"Cannot coerce {item} to {target_type}")

    def __contains__(self, item):
        return self.data.__contains__(self._coerce(item))

    def add(self, item):
        self.data.add(self._coerce(item))

    def remove(self, item):
        self.data.remove(self._coerce(item))

    def discard(self, item):
        self.data.discard(self._coerce(item))

    def update(self, *s: Iterable[T]):
        for iterable in s:
            for item in iterable:
                self.data.add(self._coerce(item))

    def intersection(self, *s: Iterable[T]) -> 'CoerciveSet[T]':
        result = self.data.intersection(self._coerce(x) for i in s for x in i)
        return self.__class__(root=result)

    def difference(self, *s: Iterable[T]) -> 'CoerciveSet[T]':
        result = self.data.difference(self._coerce(x) for i in s for x in i)
        return self.__class__(root=result)

    def symmetric_difference(self, *s: Iterable[T]) -> 'CoerciveSet[T]':
        result = self.data.symmetric_difference(
            self._coerce(x) for i in s for x in i)
        return self.__class__(root=result)

    def union(self, *s: Iterable[T]) -> 'CoerciveSet[T]':
        result = self.data.union(self._coerce(x)
                                 for iterable in s for x in iterable)
        return self.__class__(root=result)

    def __iter__(self):
        return iter(self.data)

    def __len__(self) -> int:
        return len(self.data)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.data})"


class SnowflakeSet(CoerciveSet[int]):
    """A set of Snowflakes."""

    root: Sequence[int] | Set[int]
    type: Literal["role", "user"] | None = Field(default=None)
    str_reference: dict = Field(default_factory=dict)
    # needed for type preservation in Pydantic
    # TODO: find better solution
    data: set[int] = Field(default_factory=set)

    def __init__(self, root: Iterable[int], type: Literal["role", "user"] = None, str_reference: dict = None):
        super().__init__(root=root)
        self.type = type
        self.str_reference = str_reference or {}

    def add(self, item):
        """Add an item to the set. If the item contains an ID, it will be parsed into an integer. Otherwise, it will be added as an int."""

        if getattr(item, "id", None):
            return super().add(item.id)

        return super().add(item)

    def __str__(self):
        match self.root["type"]:
            case "role":
                return ", ".join(str(self.root["str_reference"].get(i) or f"<@&{i}>") for i in self)

            case "user":
                return ", ".join(str(self.root["str_reference.get"](i) or f"<@{i}>") for i in self)

        return ", ".join(str(self.root["str_reference"].get(i) or i) for i in self)

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
