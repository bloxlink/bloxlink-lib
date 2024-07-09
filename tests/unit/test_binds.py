import pytest
from bloxlink_lib.models import binds


@pytest.fixture()
def v3_rolebinds_1() -> tuple[dict[str, dict[str, dict]], list[binds.GuildBind]]:
    return {
        "roleBinds": {
            "groups": {
                "1": {
                    "binds": {
                        "1": {
                            "roles": [
                                "566422392533024778",
                                "456584045581565957"
                            ],
                            "nickname": "sds",
                            "removeRoles": [
                                "456584045581565957"
                            ]
                        },
                        "all": {
                            "roles": [
                                "566422392533024778",
                                "456584045581565957"
                            ],
                            "nickname": "sds",
                            "removeRoles": [
                                "456584045581565957"
                            ]
                        }
                    },
                    "ranges": {},
                    "groupName": "RobloHunks",
                    "removeRoles": [
                        "456584045581565957"
                    ]
                }
            }
        }
    }, [
        binds.GuildBind(
            criteria=binds.BindCriteria(
                type="group",
                id=1,
                group=binds.GroupBindData(
                    roleset=1
                )
            ),
            nickname="sds",
            roles=[
                "566422392533024778",
                "456584045581565957"
            ],
            remove_roles=[
                "456584045581565957"
            ],
            data=binds.BindData(
                displayName="RobloHunks"
            )
        ),
        binds.GuildBind(
            criteria=binds.BindCriteria(
                type="group",
                id=1,
                group=binds.GroupBindData(
                    everyone=True
                )
            ),
            nickname="sds",
            roles=[
                "566422392533024778",
                "456584045581565957"
            ],
            remove_roles=[
                "456584045581565957"
            ],
            data=binds.BindData(
                displayName="RobloHunks"
            )
        )
    ]

@pytest.fixture()
def v3_rolebinds_2() -> tuple[dict[str, dict[str, dict]], list[binds.GuildBind]]:
    return {
        "roleBinds": {
            "groups": {
                "1": {
                    "binds": {
                        "all": {
                            "roles": [
                                "566422392533024778",
                                "456584045581565957"
                            ],
                            "nickname": "sds",
                            "removeRoles": [
                                "456584045581565957"
                            ]
                        }
                    },
                    "ranges": {},
                    "groupName": "RobloHunks",
                    "removeRoles": [
                        "456584045581565957"
                    ]
                }
            }
        }
    }, [
        binds.GuildBind(
            criteria=binds.BindCriteria(
                type="group",
                id=1,
                group=binds.GroupBindData(
                    everyone=True
                )
            ),
            nickname="sds",
            roles=[
                "566422392533024778",
                "456584045581565957"
            ],
            remove_roles=[
                "456584045581565957"
            ],
            data=binds.BindData(
                displayName="RobloHunks"
            )
        )
    ]


@pytest.fixture()
def v3_group_conversion_1() -> tuple[dict[str, dict[str, dict]], list[binds.GuildBind]]:
    """Whole group binds for V3 with 2 groups linked."""

    return {
        "groupIDs": {
            "1": {
                "nickname": "{roblox-name}-{group-rank}",
                "groupName": "Test Group 1",
                "removeRoles": []
            },
            "100": {
                "nickname": "{roblox-name}",
                "groupName": "Test Group 2",
                "removeRoles": [
                    "1111111111111111",
                    "2222222222222222"
                ]
            }
        },
    }, [
        binds.GuildBind(
            criteria=binds.BindCriteria(
                type="group",
                id=1,
                group=binds.GroupBindData(
                    dynamicRoles=True
                )
            ),
            nickname="{roblox-name}-{group-rank}",
            remove_roles=[],
            data=binds.BindData(
                displayName="Test Group 1"
            )
        ),
        binds.GuildBind(
            criteria=binds.BindCriteria(
                type="group",
                id=100,
                group=binds.GroupBindData(
                    dynamicRoles=True
                )
            ),
            nickname="{roblox-name}",
            remove_roles=[
                "1111111111111111",
                "2222222222222222"
            ],
            data=binds.BindData(
                displayName="Test Group 2"
            )
        )
    ]

@pytest.fixture()
def v3_group_conversion_2() -> tuple[dict[str, dict[str, dict]], list[binds.GuildBind]]:
    """Whole group binds for V3 with 1 group linked."""

    return {
        "groupIDs": {
            "1337": {
                "nickname": "{smart-name}",
                "groupName": "Test Group 1",
                "removeRoles": []
            },
        },
    }, [
        binds.GuildBind(
            criteria=binds.BindCriteria(
                type="group",
                id=1337,
                group=binds.GroupBindData(
                    dynamicRoles=True
                )
            ),
            nickname="{smart-name}",
            remove_roles=[],
            data=binds.BindData(
                displayName="Test Group 1"
            )
        )
    ]


class TestConvertV3WholeGroupBindsToV4:
    """Tests for converting V3 whole group binds to V4."""

    def test_whole_group_bind_length_1(self, v3_group_conversion_1): # pylint: disable=W0621
        """Test that the converted binds have the correct length."""

        v3_binds = v3_group_conversion_1[0]
        correct_v4_binds = v3_group_conversion_1[1]

        converted_binds = binds.GuildBind.from_V3(v3_binds)

        assert len(converted_binds) == len(correct_v4_binds), f"Converted binds should have {len(correct_v4_binds)} binds."

    def test_whole_group_bind_equals_another(self, v3_group_conversion_1): # pylint: disable=W0621
        """Test that the converted binds equal the same binds."""

        v3_binds = v3_group_conversion_1[0]
        correct_v4_binds = v3_group_conversion_1[1]

        converted_binds = binds.GuildBind.from_V3(v3_binds)

        assert all(
            converted_bind == correct_bind
            for converted_bind, correct_bind in zip(converted_binds, correct_v4_binds)
        )

    def test_whole_group_equals_another(self, v3_group_conversion_1): # pylint: disable=W0621
        """Test that the converted binds equal the same binds."""

        assert v3_group_conversion_1[1] == binds.GuildBind.from_V3(v3_group_conversion_1[0])

    def test_whole_group_doesnt_equal_another(self, v3_group_conversion_1, v3_group_conversion_2): # pylint: disable=W0621
        """Test that the converted binds don't equal different binds."""

        assert v3_group_conversion_1[1] != v3_group_conversion_2[1]


class TestConvertV3RoleBindsToV4:
    """Tests for converting V3 role binds to V4."""

    def test_rolebind_length_1(self, v3_rolebinds_1): # pylint: disable=W0621
        """Test that the converted binds have the correct length."""

        v3_binds = v3_rolebinds_1[0]
        correct_v4_binds = v3_rolebinds_1[1]

        converted_binds = binds.GuildBind.from_V3(v3_binds)

        assert len(converted_binds) == len(correct_v4_binds), f"Converted binds should have {len(correct_v4_binds)} binds."

    def test_role_bind_equals_another(self, v3_rolebinds_1): # pylint: disable=W0621
        """Test that the converted binds equal the correct binds."""

        v3_binds = v3_rolebinds_1[0]
        correct_v4_binds = v3_rolebinds_1[1]

        converted_binds = binds.GuildBind.from_V3(v3_binds)

        assert all(
            converted_bind == correct_bind
            for converted_bind, correct_bind in zip(converted_binds, correct_v4_binds)
        )

    def test_role_bind_doesnt_equal_different(self, v3_rolebinds_1, v3_rolebinds_2): # pylint: disable=W0621
        """Test that the converted binds don't equal different binds."""

        assert v3_rolebinds_1[1] != v3_rolebinds_2[1]
