from attrs import define, field, fields


@define(slots=True, kw_only=True)
class BaseModel: # pylint: disable=too-many-instance-attributes
    """Base representation of a model."""

    def to_dict(self) -> dict[str | int, str | int]:
        """Convert the object into a dict of values."""

        return {field.name: getattr(self, field.name) for field in fields(self.__class__)}
