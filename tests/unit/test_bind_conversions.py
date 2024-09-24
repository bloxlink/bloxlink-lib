from bloxlink_lib.models import binds
from .fixtures.binds import *


class TestConvertV3WholeGroupBindsToV4:
    """Tests for converting V3 whole group binds to V4."""

    def test_whole_group_bind_length_1(self, v3_group_conversion_1):  # pylint: disable=W0621
        """Test that the converted binds have the correct length."""

        v3_binds = v3_group_conversion_1[0]
        correct_v4_binds = v3_group_conversion_1[1]

        converted_binds = binds.GuildBind.from_V3(v3_binds)

        assert len(converted_binds) == len(
            correct_v4_binds), f"Converted binds should have {len(correct_v4_binds)} binds."

    def test_whole_group_bind_equals_another(self, v3_group_conversion_1):  # pylint: disable=W0621
        """Test that the converted binds equal the same binds."""

        v3_binds = v3_group_conversion_1[0]
        correct_v4_binds = v3_group_conversion_1[1]

        converted_binds = binds.GuildBind.from_V3(v3_binds)

        assert all(
            converted_bind == correct_bind
            for converted_bind, correct_bind in zip(converted_binds, correct_v4_binds)
        )

    def test_whole_group_equals_another(self, v3_group_conversion_1):  # pylint: disable=W0621
        """Test that the converted binds equal the same binds."""

        assert v3_group_conversion_1[1] == binds.GuildBind.from_V3(
            v3_group_conversion_1[0])

    def test_whole_group_doesnt_equal_another(self, v3_group_conversion_1, v3_group_conversion_2):  # pylint: disable=W0621
        """Test that the converted binds don't equal different binds."""

        assert v3_group_conversion_1[1] != v3_group_conversion_2[1]


class TestConvertV3RoleBindsToV4:
    """Tests for converting V3 role binds to V4."""

    def test_rolebind_length_1(self, v3_rolebinds_1):  # pylint: disable=W0621
        """Test that the converted binds have the correct length."""

        v3_binds = v3_rolebinds_1[0]
        correct_v4_binds = v3_rolebinds_1[1]

        converted_binds = binds.GuildBind.from_V3(v3_binds)

        assert len(converted_binds) == len(
            correct_v4_binds), f"Converted binds should have {len(correct_v4_binds)} binds."

    def test_role_bind_equals_another(self, v3_rolebinds_1):  # pylint: disable=W0621
        """Test that the converted binds equal the correct binds."""

        v3_binds = v3_rolebinds_1[0]
        correct_v4_binds = v3_rolebinds_1[1]

        converted_binds = binds.GuildBind.from_V3(v3_binds)

        assert all(
            converted_bind == correct_bind
            for converted_bind, correct_bind in zip(converted_binds, correct_v4_binds)
        )

    def test_role_bind_doesnt_equal_different(self, v3_rolebinds_1, v3_rolebinds_2):  # pylint: disable=W0621
        """Test that the converted binds don't equal different binds."""

        assert v3_rolebinds_1[1] != v3_rolebinds_2[1]
