from attrs import define


@define()
class Role:
    """Represents a Discord role"""

    name: str
    id: int
