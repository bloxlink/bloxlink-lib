import pytest
from bloxlink_lib.models import binds
from bloxlink_lib import database




@pytest.fixture(scope="session")
def start_docker_services(docker_services):
    """Start the Docker services."""

@pytest.fixture(scope="function")
async def wait_for_redis():
    """Wait for Redis to be ready."""

    await database.wait_for_redis()


class TestIntegrationTests:
    """Tests for converting V3 whole group binds to V4."""


    async def test_sadasda(self, start_docker_services, wait_for_redis):
        await database.update_guild_data(1, verifiedRoleName="sadasda")

        assert (await database.fetch_guild_data(1, "verifiedRoleName")).verifiedRoleName =="sadasda"
