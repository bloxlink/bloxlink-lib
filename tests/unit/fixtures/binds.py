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
