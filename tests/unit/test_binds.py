import pytest
import datetime
from bloxlink_lib.models import binds

# fixtures
from pytest_lazy_fixtures import lf, lfc
from .fixtures.members import test_discord_member
from .fixtures.roblox_users import test_roblox_user_1
from .fixtures.guilds import test_guild_1


class TestNicknames:
    """Tests related to bind nicknames."""

    @pytest.mark.parametrize("test_nickname_template,expected_nickname", [
        # roblox nickname templates
        ("{roblox-name}", lf("test_roblox_user_1.username")),
        # lfc is needed to convert to string
        ("{roblox-id}", lfc("{}".format, lf("test_roblox_user_1.id"))),
        ("{display-name}", lf("test_roblox_user_1.display_name")),
        ("{smart-name}", lfc(
            "{roblox_display_name} (@{roblox_username})".format,
            roblox_display_name=lf(
                "test_roblox_user_1.display_name"),
            roblox_username=lf(
                "test_roblox_user_1.username")
        )),
        # TODO: find a way to fix this
        # ("{roblox-age}", lfc(
        #     "{}".format,
        #     (datetime.datetime.now().replace(
        #         tzinfo=None) - test_roblox_user_1.created).days
        # )),
        ("{disable-nicknaming}", None),
        ("{group-rank}", "Guest"),

        # discord nickname templates
        ("{discord-name}", lf("test_discord_member.username")),
        ("{discord-nick}", lf("test_discord_member.nickname")),
        ("{discord-global-name}", lf("test_discord_member.global_name")),
        ("{discord-id}", lfc("{}".format, lf("test_discord_member.id"))),

        # combined
        ("[{group-rank}] {roblox-name}",
         lfc("[Guest] {}".format, lf("test_roblox_user_1.username"))),
        ("[{group-rank}] {roblox-name} {roblox-id}", lfc("[Guest] {} {}".format,
         lf("test_roblox_user_1.username"), lf("test_roblox_user_1.id"))),
    ])
    async def test_nicknames_valid_roblox_user_not_in_group(self, test_nickname_template, expected_nickname, test_discord_member, test_roblox_user_1, test_guild_1):
        """Test that the nickname is correctly parsed with a valid Roblox user."""

        test_roblox_user_1.parse_age()

        nickname = await binds.parse_template(
            guild_id=test_guild_1.id,
            guild_name=test_guild_1.name,
            member=test_discord_member,
            template=test_nickname_template,
            potential_binds=[],
            roblox_user=test_roblox_user_1,
            trim_nickname=True
        )

        assert nickname == expected_nickname
