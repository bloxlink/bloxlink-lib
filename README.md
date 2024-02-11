# Bloxlink Library
Contains the generic code used with Bloxlink. This code is not dependent on a platform (e.g. Discord) and is designed to port Bloxlink to any platform.

## What this library does
* Determines which binds apply to a user
* Connects to MongoDB and provides database fetching functions
* Allows the retrieval of Roblox entities such as badges and groups
* Provides HTTP fetching functions and utilities

## Usage
* Create an .env file in your project root with values from [this configuration file](https://github.com/bloxlink/bloxlink-lib/blob/master/bloxlink_lib/config.py)
* Import the library: `import bloxlink_lib`
* Use the library:
```py

from bloxlink_lib import get_user, RobloxGroup, fetch_typed, get_binds

# retrieve Roblox objects either using get_[identity_type] functions or using the classes:
roblox_user = await get_user(username="Roblox")
print(roblox_user.groups)

roblox_group = RobloxGroup(id=1)
await roblox_group.sync()
print(roblox_group)

# fetch an item from the internet
import pydantic
from typing import Any

class Response:
    success: bool
    error: str = None
    object: Any

obj = await fetch_typed(Response, "https://example.com")
print(obj.object)

# which binds apply to the user?
guild_binds = await get_binds(guild_id=123)
print([await b.satisfies_for(roblox_user=roblox_user, ...) for b in guild_binds])

```

<p align="left">
   <a href="https://blox.link" target="_blank">
      <img src="https://www.blox.link/bloxlink/bloxlink-2024.png" />
   </a>
</p>
