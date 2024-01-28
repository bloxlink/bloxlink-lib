from typing import TypedDict, Unpack, NotRequired


class Config(TypedDict):
    """Type definition for config values."""

    #############################
    MONGO_URL: str
    MONGO_CA_FILE: NotRequired[str]
    # these are optional because we can choose to use REDIS_URL or REDIS_HOST/REDIS_PORT/REDIS_PASSWORD
    REDIS_URL: NotRequired[str]
    REDIS_HOST: NotRequired[str]
    REDIS_PORT: NotRequired[str]
    REDIS_PASSWORD: NotRequired[str]


CONFIG: Config = None


def utils_config(config: Unpack[Config]):
    global CONFIG

    CONFIG = Config(**config)
