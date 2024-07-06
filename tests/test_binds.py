import pytest
import bloxlink_lib.models.binds as binds

@pytest.fixture()
def v3_binds():
    yield {
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
    }

class TestConvertV3BindsToV4:
    def test_that_depends_on_resource(self, v3_binds):
        assert True

