from os import getcwd
from dotenv import dotenv_values
from .models.base import BaseModel

__all__ = ("CONFIG",)

class Config(BaseModel):
    """Type definition for config values."""

    DISCORD_TOKEN: str
    #############################
    MONGO_URL: str
    MONGO_CA_FILE: str = None
    # these are optional because we can choose to use REDIS_URL or REDIS_HOST/REDIS_PORT/REDIS_PASSWORD
    REDIS_URL: str = None
    REDIS_HOST: str = None
    REDIS_PORT: str = None
    REDIS_PASSWORD: str = None
    #############################
    PROXY_URL: str = None
    ROBLOX_INFO_SERVER: str


CONFIG: Config = Config(
    **{field:value for field, value in dotenv_values(f"{getcwd()}/.env").items() if field in Config.__annotations__}
)
