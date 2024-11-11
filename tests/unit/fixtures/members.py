import pytest
from bloxlink_lib import MemberSerializable
from .guilds import test_guild_1


@pytest.fixture(params=[
    1389419438194318
])
def test_discord_member(request, test_guild_1) -> MemberSerializable:
    """Test Discord Member model."""

    return MemberSerializable(
        id=request.param,
        global_name="Bob",
        username="bob",
        avatar_url="https://cdn.discordapp.com/avatars/123/abc.png",
        is_bot=False,
        joined_at="2021-01-01T00:00:00.000000+00:00",
        role_ids=["123", "456"],
        guild_id=test_guild_1.id,
        nickname="bobby",
        mention=f"<@{request.param}>",
    )
