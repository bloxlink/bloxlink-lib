from typing import Sequence, Self, TypedDict, Dict
import math
from datetime import datetime
import hikari
from attrs import field, define, asdict
from dateutil import parser
from .base import BaseModel
from ..fetch import fetch, fetch_typed, StatusCodes
from ..config import CONFIG
from ..exceptions import RobloxNotFound, RobloxAPIError, UserNotVerified
from ..database import fetch_user_data, mongo
from .groups import RobloxGroup

ALL_USER_API_SCOPES = ["groups", "badges"]


@define(slots=True)
class UserData:
    """Representation of a User's data in Bloxlink

    Attributes:
        id (int): The Discord ID of the user.
        robloxID (str): The roblox ID of the user's primary account.
        robloxAccounts (dict): All of the user's linked accounts, and any guild specific verifications.
    """

    id: int
    robloxID: str = None
    robloxAccounts: dict = field(factory=lambda: {"accounts": [], "guilds": {}, "confirms": {}})


class RobloxResponseDict(TypedDict, total=False):
    """Type definition for a Roblox user from the Roblox API."""

    id: str
    name: str
    description: str
    isBanned: bool
    profileLink: str
    badges: list
    displayName: str
    created: str
    avatar: dict

@define(kw_only=True)
class RobloxUser(BaseModel): # pylint: disable=too-many-instance-attributes
    """Representation of a user on Roblox."""

    id: str = field(converter=str)
    username: str = None
    banned: bool = None
    age_days: int = None
    groups: dict = None
    avatar: str = None
    description: str = None
    profile_link: str = None
    display_name: str = None
    created: str = None
    badges: list = None
    short_age_string: str = None

    complete: bool = False

    _data: RobloxResponseDict = field(factory=lambda: {})

    async def sync(
        self,
        includes: list | bool | None = None,
        *,
        cache: bool = True,
    ):
        """Retrieve information about this user from Roblox. Requires a username or id to be set.

        Args:
            includes (list | bool | None, optional): Data that should be included. Defaults to None.
                True retrieves all available data. Otherwise a list can be passed with either
                "groups", "presences", and/or "badges" in it.
            cache (bool, optional): Should we check the object for values before retrieving. Defaults to True.
        """
        if includes is None:
            includes = []

        elif includes is True:
            includes = ALL_USER_API_SCOPES
            self.complete = True

        if cache:
            # remove includes if we already have the value saved
            if self.groups is not None and "groups" in includes:
                includes.remove("groups")

            if self.badges is not None and "badges" in includes:
                includes.remove("badges")

        includes = ",".join(includes)

        id_string = "id" if not self.id else f"id={self.id}"
        username_string = "username" if not self.username else f"username={self.username}"

        roblox_user_data, user_data_response = await fetch_typed(
            f"{CONFIG.ROBLOX_INFO_SERVER}/roblox/info?{id_string}&{username_string}&include={includes}",
            RobloxResponseDict,
        )

        if user_data_response.status == StatusCodes.OK:
            self.id = roblox_user_data.get("id", self.id)
            self.description = roblox_user_data.get("description", self.description)
            self.username = roblox_user_data.get("name", self.username)
            self.banned = roblox_user_data.get("isBanned", self.banned)
            self.profile_link = roblox_user_data.get("profileLink", self.profile_link)
            self.badges = roblox_user_data.get("badges", self.badges)
            self.display_name = roblox_user_data.get("displayName", self.display_name)
            self.created = roblox_user_data.get("created", self.created)

            self._data.update(roblox_user_data)

            await self.parse_groups(roblox_user_data.get("groups"))

            self.parse_age()

            avatar = roblox_user_data.get("avatar")

            if avatar:
                avatar_url, avatar_response = await fetch("GET", avatar["bustThumbnail"])

                if avatar_response.status == StatusCodes.OK:
                    self.avatar = avatar_url.get("data", [{}])[0].get("imageUrl")

    def parse_age(self):
        """Set a human-readable string representing how old this account is."""
        if (self.age_days is not None) or not self.created:
            return

        today = datetime.today()
        roblox_user_age = parser.parse(self.created).replace(tzinfo=None)
        self.age_days = (today - roblox_user_age).days

        self._data.update({"age_days": self.age_days})

        if not self.short_age_string:
            if self.age_days >= 365:
                years = math.floor(self.age_days / 365)
                ending = f"yr{((years > 1 or years == 0) and 's') or ''}"
                self.short_age_string = f"{years} {ending} ago"
            else:
                ending = f"day{((self.age_days > 1 or self.age_days == 0) and 's') or ''}"
                self.short_age_string = f"{self.age_days} {ending} ago"

    async def parse_groups(self, group_json: dict | None):
        """Determine what groups this user is in from a json response.

        Args:
            group_json (dict | None): JSON input from Roblox representing a user's groups.
        """
        if group_json is None:
            return

        self.groups = {}

        for group_data in group_json:
            group_meta = group_data.get("group")
            group_role = group_data.get("role")

            group: RobloxGroup = RobloxGroup(
                id=str(group_meta["id"]),
                name=group_meta["name"],
                user_roleset=group_role,
            )  # seems redundant, but this is so we can switch the endpoint and retain consistency
            await group.sync()
            self.groups[group.id] = group

    def to_dict(self) -> Dict[Self]:
        """Return a dictionary representing this roblox account"""
        return asdict(self)


async def get_user_account(
    user: hikari.User | str, guild_id: int = None, raise_errors=True
) -> RobloxUser | None:
    """Get a user's linked Roblox account.

    Args:
        user (hikari.User | str): The User or user ID to find the linked Roblox account for.
        guild_id (int, optional): Used to determine what account is linked in the given guild id.
            Defaults to None.
        raise_errors (bool, optional): Should errors be raised or not. Defaults to True.

    Raises:
        UserNotVerified: If raise_errors and user is not linked with Bloxlink.

    Returns:
        RobloxUser | None: The linked Roblox account either globally or for this guild, if any.
    """

    user_id = str(user.id) if isinstance(user, hikari.User) else str(user)
    bloxlink_user = await fetch_user_data(user_id, "robloxID", "robloxAccounts")

    if guild_id:
        guild_accounts = (bloxlink_user.robloxAccounts or {}).get("guilds") or {}

        guild_account = guild_accounts.get(str(guild_id))

        if guild_account:
            return RobloxUser(id=guild_account)

    if bloxlink_user.robloxID:
        return RobloxUser(id=bloxlink_user.robloxID)

    if raise_errors:
        raise UserNotVerified()

    return None

async def get_user(
    user: hikari.User = None,
    includes: list = None,
    *,
    roblox_username: str = None,
    roblox_id: int = None,
    guild_id: int = None,
) -> RobloxUser:
    """Get a Roblox account.

    If a user is not passed, it is required that either roblox_username OR roblox_id is given.

    roblox_id takes priority over roblox_username when searching for users.

    guild_id only applies when a user is given.

    Args:
        user (hikari.User, optional): Get the account linked to this user. Defaults to None.
        includes (list | bool | None, optional): Data that should be included. Defaults to None.
            True retrieves all available data. Otherwise a list can be passed with either
            "groups", "presences", and/or "badges" in it.
        roblox_username (str, optional): Username of the account to get. Defaults to None.
        roblox_id (int, optional): ID of the account to get. Defaults to None.
        guild_id (int, optional): Guild ID if looking up a user to determine the linked account in that guild.
            Defaults to None.

    Returns:
        RobloxAccount | None: The found Roblox account, if any.
    """

    roblox_account: RobloxUser = None

    if user:
        roblox_account = await get_user_account(user, guild_id)
        await roblox_account.sync(includes)

    else:
        roblox_account = RobloxUser(username=roblox_username, id=roblox_id)
        await roblox_account.sync(includes)

    return roblox_account


async def get_accounts(user: hikari.User) -> list[RobloxUser]:
    """Get a user's linked Roblox accounts.

    Args:
        user (hikari.User): The user to get linked accounts for.

    Returns:
        list[RobloxAccount]: The linked Roblox accounts for this user.
    """

    user_id = str(user.id)
    bloxlink_user = await fetch_user_data(user_id, "robloxID", "robloxAccounts")

    account_ids = set()

    if bloxlink_user.robloxID:
        account_ids.add(bloxlink_user.robloxID)

    guild_accounts = (bloxlink_user.robloxAccounts or {}).get("guilds") or {}

    for guild_account_id in guild_accounts.values():
        account_ids.add(guild_account_id)

    accounts = [
        RobloxUser(id=account_id) for account_id in account_ids
    ]

    return accounts


async def reverse_lookup(roblox_account: RobloxUser, exclude_user_id: int | None = None) -> list[str]:
    """Find Discord IDs linked to a roblox id.

    Args:
        roblox_account (RobloxAccount): The roblox account that will be matched against.
        exclude_user_id (int | None, optional): Discord user ID that will not be included in the output.
            Defaults to None.

    Returns:
        list[str]: All the discord IDs linked to this roblox_id.
    """
    cursor = mongo.bloxlink["users"].find(
        {"$or": [{"robloxID": roblox_account.id}, {"robloxAccounts.accounts": roblox_account.id}]},
        {"_id": 1},
    )

    return [x["_id"] async for x in cursor if str(exclude_user_id) != str(x["_id"])]

async def get_user_from_string(target: str) -> RobloxUser:
    """Get a RobloxAccount from a given target string (either an ID or username)

    Args:
        target (str): Roblox ID or username of the account to sync.

    Raises:
        RobloxNotFound: When no user is found.
        *Other exceptions may be raised such as RobloxAPIError from get_user*

    Returns:
        RobloxAccount: The synced RobloxAccount of the user requested.
    """
    account = None

    if target.isdigit():
        try:
            account = await get_user(roblox_id=target)
        except (RobloxNotFound, RobloxAPIError):
            pass

    # Fallback to parse input as a username if the input was not a valid id.
    if account is None:
        try:
            account = await get_user(roblox_username=target)
        except RobloxNotFound as exc:
            raise RobloxNotFound(
                "The Roblox user you were searching for does not exist! "
                "Please check the input you gave and try again!"
            ) from exc

    if account.id is None or account.username is None:
        raise RobloxNotFound("The Roblox user you were searching for does not exist.")

    return account



@define(kw_only=True)
class MemberSerializable(BaseModel):
    id: hikari.Snowflake = field(converter=int)
    username: str = None
    avatar_url: str = None
    display_name: str = None
    is_bot: bool = None
    joined_at: str = None
    role_ids: Sequence[hikari.Snowflake] = None
    guild_id: int = None
    avatar_hash: str = None
    nickname: str = None

    @staticmethod
    def from_hikari(member: hikari.InteractionMember | Self) -> 'MemberSerializable':
        """Convert a Hikari member into a MemberSerializable object."""

        if isinstance(member, MemberSerializable):
            return member

        return MemberSerializable(
            id=member.id,
            username=member.username,
            avatar_url=str(member.avatar_url),
            display_name=member.display_name,
            is_bot=member.is_bot,
            joined_at=member.joined_at,
            role_ids=member.role_ids,
            guild_id=member.guild_id,
            avatar_hash=member.avatar_hash,
            nickname=member.nickname
        )
