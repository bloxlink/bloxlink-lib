import json

from bloxlink_lib import GuildBind

old_json_data = """{
    "roleBinds": {
        "groups": {
            "3587262": {
                "groupName": "Bloxlink Space",
                "binds": {
                    "all": {
                        "nickname": "joe mama",
                        "roles": [],
                        "removeRoles": []
                    },
                    "0": {
                        "nickname": null,
                        "roles": [
                            "895572042382979092"
                        ],
                        "removeRoles": []
                    },
                    "150": {
                        "nickname": null,
                        "roles": [
                            "894379486466940938"
                        ],
                        "removeRoles": []
                    },
                    "-1": {
                        "nickname": null,
                        "roles": [
                            "894379486466940938"
                        ],
                        "removeRoles": []
                    }
                },
                "ranges": [
                    {
                        "high": 200,
                        "low": 25,
                        "nickname": null,
                        "removeRoles": [],
                        "roles": [
                            "895572042382979092"
                        ]
                    }
                ],
                "removeRoles": []
            }
        },
        "assets": {
            "10193400881": {
                "displayName": "Fragmented Top Hat",
                "nickname": null,
                "roles": [
                    "894379486466940938"
                ],
                "removeRoles": []
            }
        },
        "badges": {
            "2129742571": {
                "displayName": "THE SNITCH",
                "nickname": null,
                "roles": [
                    "899869705723076608"
                ],
                "removeRoles": []
            }
        },
        "gamePasses": {
            "28005026": {
                "displayName": "More Decks & +99 Card",
                "nickname": null,
                "roles": [
                    "894379486466940938"
                ],
                "removeRoles": []
            }
        }
    },
    "groupIDs": {
        "3250440": {
            "groupName": "Bloxlink Misc",
            "nickname": null,
            "removeRoles": []
        },
        "3587262": {
            "groupName": "Bloxlink Space",
            "nickname": null,
            "removeRoles": []
        }
    }
}
"""


def convert_old_to_new() -> list:
    json_data = json.loads(old_json_data)
    output = []

    full_groups = json_data.get("groupIDs", {})
    rolebinds = json_data.get("roleBinds", {})

    group_rb = rolebinds.get("groups", {})
    asset_rb = rolebinds.get("assets", {})
    badge_rb = rolebinds.get("badges", {})
    gamep_rb = rolebinds.get("gamePasses", {})

    for group_id, bind_data in full_groups.items():
        output.append(GuildBind.from_V3("groupIDs", group_id, bind_data))

    for entity_id, bind_data in asset_rb.items():
        output.append(GuildBind.from_V3("assets", entity_id, bind_data))

    for entity_id, bind_data in badge_rb.items():
        output.append(GuildBind.from_V3("badges", entity_id, bind_data))

    for entity_id, bind_data in gamep_rb.items():
        output.append(GuildBind.from_V3("gamePasses", entity_id, bind_data))

    for group_id, bind_data in group_rb.items():
        if bind_data.get("binds"):
            for rank_id, criteria_data in bind_data["binds"].items():
                output.append(GuildBind.from_V3_group_rolebind("roleset", group_id, {rank_id: criteria_data}))

        if bind_data.get("ranges"):
            for criteria_data in bind_data["ranges"]:
                output.append(GuildBind.from_V3_group_rolebind("range", group_id, criteria_data))

    return output


print("\n".join([repr(x) for x in convert_old_to_new()]))
