from __future__ import annotations

import asyncio
import datetime
import json
from os.path import exists
from typing import Type, TYPE_CHECKING, Any

from motor.motor_asyncio import AsyncIOMotorClient
from redis.asyncio import Redis
from redis import ConnectionError as RedisConnectionError

from bloxlink_lib.models import users, guilds
from bloxlink_lib import BaseModel
from .config import CONFIG

mongo: AsyncIOMotorClient = None
redis: Redis = None

if TYPE_CHECKING:
    from . import MemberSerializable, GuildSerializable


def connect_database():
    global mongo # pylint: disable=global-statement
    global redis # pylint: disable=global-statement

    loop = asyncio.get_event_loop()

    if CONFIG.MONGO_CA_FILE:
        ca_file = exists("cert.crt")

        if not ca_file:
            with open("src/cert.crt", "w") as f:
                f.write(CONFIG.MONGO_CA_FILE)

    mongo = AsyncIOMotorClient(CONFIG.MONGO_URL, tlsCAFile="src/cert.crt" if CONFIG.MONGO_CA_FILE else None)
    mongo.get_io_loop = asyncio.get_running_loop

    if CONFIG.REDIS_URL:
        redis = Redis.from_url(
            CONFIG.REDIS_URL,
            decode_responses=True,
            retry_on_timeout=True,
            health_check_interval=30,
        )
    else:
        redis = Redis(
            host=CONFIG.REDIS_HOST,
            port=CONFIG.REDIS_PORT,
            password=CONFIG.REDIS_PASSWORD,
            decode_responses=True,
            retry_on_timeout=True,
            health_check_interval=30,
        )

    # override redis with better set method
    redis._old_set = redis.set # pylint: disable=protected-access
    redis.set = redis_set

    loop.create_task(_heartbeat_loop())

async def redis_set(key: str, value: BaseModel | Any, expire: datetime.timedelta | int=None, **kwargs):
    """Set a value in Redis. Accepts BaseModels and expirations as datetimes."""

    await redis._old_set(key, # pylint: disable=protected-access
                         value.model_dump_json() if isinstance(value, BaseModel) else json.dumps(value),
                         ex=int(expire.total_seconds()) if expire and isinstance(expire, datetime.timedelta) else expire,
                         **kwargs)

async def _heartbeat_loop():
    while True:
        try:
            await asyncio.wait_for(redis.ping(), timeout=10)
        except RedisConnectionError as e:
            raise SystemError("Failed to connect to Redis.") from e

        await asyncio.sleep(5)

async def fetch_item[T](domain: str, constructor: Type[T], item_id: str, *aspects) -> T:
    """
    Fetch an item from local cache, then redis, then database.
    Will populate caches for later access
    """
    # should check local cache but for now just fetch from redis

    if aspects:
        item = await redis.hmget(f"{domain}:{item_id}", *aspects)
        item = {x: y for x, y in zip(aspects, item) if y is not None}
    else:
        item = await redis.hgetall(f"{domain}:{item_id}")

    if not item:
        item = await mongo.bloxlink[domain].find_one({"_id": item_id}, {x: True for x in aspects}) or {
            "_id": item_id
        }

        if item and not isinstance(item, (list, dict)):
            if aspects:
                items = {x: item[x] for x in aspects if item.get(x) and not isinstance(item[x], dict)}

                if items:
                    async with redis.pipeline() as pipeline:
                        await pipeline.hmset(f"{domain}:{item_id}", items)
                        await pipeline.expire(f"{domain}:{item_id}", datetime.timedelta(hours=1).total_seconds())
                        await pipeline.execute()
            else:
                async with redis.pipeline() as pipeline:
                    await pipeline.hmset(f"{domain}:{item_id}", item)
                    await pipeline.expire(f"{domain}:{item_id}", datetime.timedelta(hours=1).total_seconds())
                    await pipeline.execute()

    if item.get("_id"):
        item.pop("_id")

    item["id"] = item_id

    return constructor(**item)


async def update_item(domain: str, item_id: str, **aspects) -> None:
    """
    Update an item's aspects in local cache, redis, and database.
    """
    unset_aspects = {}
    set_aspects = {}

    for key, val in aspects.items():
        if val is None:
            unset_aspects[key] = ""
        else:
            set_aspects[key] = val

    # Update redis cache
    redis_set_aspects = {}
    redis_unset_aspects = {}

    for aspect_name, aspect_value in dict(aspects).items():
        if aspect_value is None:
            redis_unset_aspects[aspect_name] = aspect_value
        elif isinstance(aspect_value, (dict, list, bool)):
            pass
        else:
            redis_set_aspects[aspect_name] = aspect_value

    if redis_set_aspects:
        async with redis.pipeline() as pipeline:
            await pipeline.hset(f"{domain}:{item_id}", mapping=redis_set_aspects)
            await pipeline.expire(f"{domain}:{item_id}", datetime.timedelta(hours=1).total_seconds())
            await pipeline.execute()

    if redis_unset_aspects:
        await redis.hdel(f"{domain}:{item_id}", *redis_unset_aspects.keys())

    # update database
    await mongo.bloxlink[domain].update_one(
        {"_id": item_id}, {"$set": set_aspects, "$unset": unset_aspects}, upsert=True
    )


async def fetch_user_data(user: str | int | dict | MemberSerializable, *aspects) -> users.UserData:
    """
    Fetch a full user from local cache, then redis, then database.
    Will populate caches for later access
    """

    if isinstance(user, dict):
        user_id = str(user["id"])
    elif isinstance(user, users.MemberSerializable):
        user_id = str(user.id)
    else:
        user_id = str(user)

    return await fetch_item("users", users.UserData, user_id, *aspects)


async def fetch_guild_data(guild: str | int | dict | GuildSerializable, *aspects) -> guilds.GuildData:
    """
    Fetch a full guild from local cache, then redis, then database.
    Will populate caches for later access
    """

    if isinstance(guild, dict):
        guild_id = str(guild["id"])
    elif isinstance(guild, guilds.GuildSerializable):
        guild_id = str(guild.id)
    else:
        guild_id = str(guild)

    return await fetch_item("guilds", guilds.GuildData, guild_id, *aspects)


async def update_user_data(user: str | int | dict | MemberSerializable, **aspects) -> None:
    """
    Update a user's aspects in local cache, redis, and database.
    """

    if isinstance(user, dict):
        user_id = str(user["id"])
    elif isinstance(user, users.MemberSerializable):
        user_id = str(user.id)
    else:
        user_id = str(user)

    return await update_item("users", user_id, **aspects)


async def update_guild_data(guild: str | int | dict | GuildSerializable, **aspects) -> None:
    """
    Update a guild's aspects in local cache, redis, and database.
    """

    if isinstance(guild, dict):
        guild_id = str(guild["id"])
    elif isinstance(guild, guilds.GuildSerializable):
        guild_id = str(guild.id)
    else:
        guild_id = str(guild)

    return await update_item("guilds", guild_id, **aspects)



connect_database()
