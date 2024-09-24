import pytest
from bloxlink_lib import RobloxUser


@pytest.fixture()
def test_roblox_user() -> RobloxUser:
    """Test RobloxUser model."""

    return RobloxUser(
        id=100,
        username="john",
        display_name="John Doe",
        join_date="2021-01-01T00:00:00.000000+00:00"
    )
