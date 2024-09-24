import pytest
from bloxlink_lib.models.guilds import GuildSerializable, RoleSerializable


@pytest.fixture()
def test_guild() -> GuildSerializable:
    return GuildSerializable(
        id=1,
        name="My awesome server",
        roles={
            1: RoleSerializable(
                id=1,
                name="Admin",
                color=0xFF0000,
                is_hoisted=True,
                position=1,
                permissions=0,
                is_managed=False,
                is_mentionable=True
            )
        }
    )
