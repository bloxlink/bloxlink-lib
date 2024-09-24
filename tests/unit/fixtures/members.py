import pytest
from bloxlink_lib import MemberSerializable


@pytest.fixture()
def member_bob() -> MemberSerializable:
    """Whole group binds for V3 with 1 group linked."""

    member_id = 1

    return MemberSerializable(
        id=member_id,
        username="bob",
        avatar_url="https://cdn.discordapp.com/avatars/123/abc.png",
        display_name="Bob",
        is_bot=False,
        joined_at="2021-01-01T00:00:00.000000+00:00",
        role_ids=["123", "456"],
        guild_id=123,
        nickname=None,
        mention=f"<@{member_id}>",
    )
