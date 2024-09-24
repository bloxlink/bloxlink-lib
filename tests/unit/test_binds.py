from bloxlink_lib.models import binds
from .fixtures.binds import *


class TestGroupBinds:
    """Tests related to group binds."""

    def test_whole_group_success_1(self, v3_group_conversion_1): # pylint: disable=W0621
        """Test that the converted binds have the correct length."""

        v3_binds = v3_group_conversion_1[0]
        correct_v4_binds = v3_group_conversion_1[1]

        converted_binds = binds.GuildBind.from_V3(v3_binds)

        assert len(converted_binds) == len(correct_v4_binds), f"Converted binds should have {len(correct_v4_binds)} binds."
