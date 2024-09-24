import pytest
from bloxlink_lib import database
from pydantic import ValidationError



class TestUpdatingGuildData:
    """Tests for converting V3 whole group binds to V4."""


    @pytest.mark.parametrize("test_input", [
        "sadasda",
        "Very awesome role"
    ])
    async def test_update_guild_data(self, test_input, start_docker_services, wait_for_redis):
        await database.update_guild_data(1, verifiedRoleName=test_input)

        assert (await database.fetch_guild_data(1, "verifiedRoleName")).verifiedRoleName == test_input

    @pytest.mark.parametrize("test_input", [
        # 5,
        # 0,
        pytest.param(-1, marks=pytest.mark.xfail)
    ])
    @pytest.mark.xfail(raises=ValidationError) 
    async def test_update_guild_data_fails(self, test_input, start_docker_services, wait_for_redis):
        await database.update_guild_data(1, verifiedRoleName=test_input)

        assert (await database.fetch_guild_data(1, "verifiedRoleName")).verifiedRoleName == test_input
