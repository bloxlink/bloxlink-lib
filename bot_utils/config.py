from attrs import define
from dotenv import dotenv_values
from os import getcwd


@define(slots=True, kw_only=True)
class Config:
    """Type definition for config values."""

    #############################
    MONGO_URL: str
    MONGO_CA_FILE: str = None
    # these are optional because we can choose to use REDIS_URL or REDIS_HOST/REDIS_PORT/REDIS_PASSWORD
    REDIS_URL: str = None
    REDIS_HOST: str = None
    REDIS_PORT: str = None
    REDIS_PASSWORD: str = None


CONFIG: Config = Config(
    **{field:value for field, value in dotenv_values(f"{getcwd()}/.env").items() if field in Config.__annotations__}
)
