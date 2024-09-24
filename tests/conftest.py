import asyncio
import pytest
from bloxlink_lib import database

@pytest.fixture(scope='session')
def event_loop(request):
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
def start_docker_services(docker_services):
    """Start the Docker services."""

@pytest.fixture(scope="function")
async def wait_for_redis():
    """Wait for Redis to be ready."""

    await database.wait_for_redis()