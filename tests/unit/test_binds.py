import pytest
from bloxlink_lib.models import binds
from .fixtures.members import member_bob
from .fixtures.roblox_users import test_roblox_user
from .fixtures.guilds import test_guild


class TestNicknames:
    """Tests related to bind nicknames."""

    @pytest.mark.parametrize("test_input,expected", [
        ("{roblox-name}", "bob"),
        ("{roblox-id}", "1"),
    ])
    async def test_nicknames_valid_roblox_user(self, test_input, expected, member_bob, test_roblox_user):
        """."""

        nickname = await binds.parse_template(
            guild_id=test_guild.id,
            guild_name=test_guild.name,
            member=member_bob,
            template="{roblox-name}",
            potential_binds=[],
            roblox_user=None,
            max_length=True
        )

        assert nickname == "bob"
