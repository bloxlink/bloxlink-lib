from os import getcwd
from typing import Literal
from dotenv import dotenv_values
from .models.base import BaseModel

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
    DISCORD_PROXY_URL: str = None
    ROBLOX_INFO_SERVER: str
    #############################
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    def model_post_init(self, __context):
        # easier to validate with python expressions instead of attrs validators
        if self.REDIS_URL is None and (
            self.REDIS_HOST is None or self.REDIS_PORT is None
        ):
            raise ValueError("REDIS_URL or REDIS_HOST/REDIS_PORT/REDIS_PASSWORD must be set")

        if all([self.REDIS_HOST, self.REDIS_PORT, self.REDIS_PASSWORD, self.REDIS_URL]):
            raise ValueError("REDIS_URL and REDIS_HOST/REDIS_PORT/REDIS_PASSWORD cannot both be set")


CONFIG: Config = Config(
    **{field:value for field, value in dotenv_values(f"{getcwd()}/.env").items() if field in Config.__annotations__}
)
