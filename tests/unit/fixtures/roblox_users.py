from datetime import datetime
import pytest
from bloxlink_lib import RobloxUser


@pytest.fixture()
def test_roblox_user_1() -> RobloxUser:
    """Test RobloxUser model."""

    return RobloxUser(
        id=100,
        username="john",
        display_name="John Doe",
        created=datetime.fromisoformat(
            "2021-01-01T00:00:00.000000+00:00").replace(tzinfo=None)
    )
