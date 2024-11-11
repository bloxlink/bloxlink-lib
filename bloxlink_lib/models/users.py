from __future__ import annotations

from typing import Sequence, Self, Annotated, Literal, TYPE_CHECKING
from pydantic import Field
import math
from datetime import datetime
import hikari
import discord
from ..fetch import fetch, fetch_typed, StatusCodes
from ..config import CONFIG
from ..exceptions import RobloxNotFound, RobloxAPIError, UserNotVerified
from ..database import fetch_user_data, mongo
from .groups import GroupRoleset
from .base import Snowflake, BaseModel

if TYPE_CHECKING:
    from .base_assets import RobloxBaseAsset

VALID_INFO_SERVER_SCOPES: list[Literal["groups", "badges"]] = [
    "groups", "badges"]
INVENTORY_API = "https://inventory.roblox.com"
USERS_API = "https://users.roblox.com"
USERS_BASE_DATA_API = USERS_API + "/v1/users/{roblox_id}"
USER_GROUPS_API = "https://groups.roblox.com/v2/users/{roblox_id}/groups/roles"
USER_BADGES_API = "https://www.roblox.com/badges/roblox?userId={roblox_id}"
AVATAR_URLS = {
    "bustThumbnail": "https://thumbnails.roblox.com/v1/users/avatar-bust?userIds={roblox_id}&size=420x420&format=Png&isCircular=false",
    "headshotThumbnail": "https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds={roblox_id}&size=420x420&format=Png&isCircular=false",
    "fullBody": "https://thumbnails.roblox.com/v1/users/avatar?userIds={roblox_id}&size=720x720&format=Png&isCircular=false"
}


class UserData(BaseModel):
    """Representation of a User's data in Bloxlink

    Attributes:
        id (int): The Discord ID of the user.
        robloxID (str): The roblox ID of the user's primary account.
        robloxAccounts (dict): All of the user's linked accounts, and any guild specific verifications.
    """

    id: int
    robloxID: str | None = None
    robloxAccounts: dict = Field(default_factory=lambda: {
                                 "accounts": [], "guilds": {}, "confirms": {}})


class UserAvatar(BaseModel):
    """Type definition for a Roblox user's avatar from the Bloxlink Info API."""

    bust_thumbnail: str | None = Field(alias="bustThumbnail")
    headshot_thumbnail: str | None = Field(alias="headshotThumbnail")
    full_body: str | None = Field(alias="fullBody")


class RobloxUserAvatar(BaseModel):
    """Type definition for a Roblox avatar from the Roblox API."""

    target_id: int = Field(alias="targetId")
    state: str
    image_url: str = Field(alias="imageUrl")


class RobloxUserAvatarResponse(BaseModel):
    """Type definition for a Roblox user's avatar from the Roblox API."""

    data: list[RobloxUserAvatar]


class RobloxGroupResponse(BaseModel):
    id: int
    name: str
    member_count: int = Field(alias="memberCount")
    has_verified_badge: bool = Field(alias="hasVerifiedBadge")


class RobloxUserGroups(BaseModel):
    """Type definition for a Roblox group from a user from the Roblox API."""

    group: RobloxGroupResponse
    role: GroupRoleset


class RobloxUserGroupsResponse(BaseModel):
    """Type definition for a Roblox user's groups from the Roblox API."""

    data: list[RobloxUserGroups]


class RobloxUserBadge(BaseModel):
    """Type definition for a Roblox badge from the Roblox API."""

    image_url: str = Field(alias="ImageUri")
    name: str = Field(alias="Name")


class RobloxUserBadgeResponse(BaseModel):
    """Type definition for a Roblox user's badges from the Roblox API."""

    RobloxBadges: list[RobloxUserBadge]


class RobloxUser(BaseModel):  # pylint: disable=too-many-instance-attributes
    """Representation of a user on Roblox."""

    # must provide one of these
    id: int | None = None
    username: str | None = Field(default=None, alias="name")

    # these fields are provided after sync() is called
    banned: bool = Field(alias="isBanned", default=False)
    age_days: int = None
    groups: dict[int, RobloxUserGroups] | None = Field(default=None)

    avatar: UserAvatar = None
    avatar_url: str | None = None

    description: str | None = None
    profile_link: str = Field(alias="profileLink", default=None)
    display_name: str | None = Field(alias="displayName", default=None)
    created: datetime = None
    badges: list | None = None
    short_age_string: str = None

    _complete: bool = False

    async def sync(
        self,
        includes: list[Literal["groups", "badges"]] | bool | None = None,
        *,
        cache: bool = True
    ):
        """Retrieve and sync information about this user from Roblox. Requires a username or id to be set.

        Args:
            includes (list | bool | None, optional): Data that should be included. Defaults to None.
                True retrieves all available data; otherwise, a list can be passed with either
                "groups", "presences", and/or "badges" in it.
            cache (bool, optional): Should we check the object for values before retrieving. Defaults to True.
        """

        if includes is not None and any((x is False or x not in [*VALID_INFO_SERVER_SCOPES, True, None]) for x in includes):
            raise ValueError("Invalid includes provided.")

        if includes is None:
            includes = []

        elif includes is True:
            includes = VALID_INFO_SERVER_SCOPES
            self._complete = True

        if cache:
            # remove includes if we already have the value saved
            if self.groups is not None and "groups" in includes:
                includes.remove("groups")

            if self.badges is not None and "badges" in includes:
                includes.remove("badges")

        roblox_user_data, user_data_response = await fetch_typed(
            RobloxUser,
            f"{CONFIG.BOT_API}/users",
            headers={"Authorization": CONFIG.BOT_API_AUTH},
            params={"id": self.id, "username": self.username,
                    "include": ",".join(includes)},
        )

        if user_data_response.status == StatusCodes.OK:
            self.id = roblox_user_data.id or self.id
            self.description = roblox_user_data.description or self.description
            self.username = roblox_user_data.username or self.username
            self.banned = roblox_user_data.banned or self.banned
            self.badges = roblox_user_data.badges or self.badges
            self.display_name = roblox_user_data.display_name or self.display_name or self.username
            self.created = roblox_user_data.created or self.created
            self.avatar = roblox_user_data.avatar or self.avatar
            self.profile_link = roblox_user_data.profile_link or self.profile_link
            self.groups = roblox_user_data.groups or self.groups

            self.parse_age()

            avatar = roblox_user_data.avatar

            if avatar:
                avatar_url, avatar_response = await fetch("GET", avatar.bust_thumbnail)

                if avatar_response.status == StatusCodes.OK:
                    self.avatar_url = avatar_url.get(
                        "data", [{}])[0].get("imageUrl") or None

    async def owns_asset(self, asset: RobloxBaseAsset) -> bool:
        """Check if the user owns a specific asset.

        Args:
            asset (RobloxBaseAsset): The asset to check for.

        Returns:
            bool: If the user owns the asset or not.
        """

        try:
            response_data, _ = await fetch(
                "GET",
                f"{INVENTORY_API}/v1/users/{self.id}/items/{asset.type_number}/{asset.id}/is-owned",
                parse_as="TEXT"
            )
        except RobloxAPIError:
            return False

        return response_data == "true"

    def parse_age(self):
        """Set a human-readable string representing how old this account is."""
        if (self.age_days is not None) or not self.created:
            return

        today = datetime.today()
        self.age_days = (today - self.created).days

        if not self.short_age_string:
            if self.age_days >= 365:
                years = math.floor(self.age_days / 365)
                ending = f"yr{((years > 1 or years == 0) and 's') or ''}"
                self.short_age_string = f"{years} {ending} ago"
            else:
                ending = f"day{
                    ((self.age_days > 1 or self.age_days == 0) and 's') or ''}"
                self.short_age_string = f"{self.age_days} {ending} ago"


class RobloxUsernameData(BaseModel):
    requestedUsername: str
    hasVerifiedBadge: bool
    id: int
    name: str
    displayName: str


class RobloxUsernameResponse(BaseModel):
    data: list[RobloxUsernameData]


# fetch functions. these should not be used directly in commands; instead, get_user() should be used instead
async def fetch_roblox_id(roblox_username: str) -> int | None:
    """Fetch a Roblox ID from a Roblox username."""

    username_data, username_response = await fetch_typed(
        RobloxUsernameResponse,
        f"{USERS_API}/v1/usernames/users",
        method="POST",
        body={
            "usernames": [
                roblox_username
            ],
            "excludeBannedUsers": False
        }
    )

    if username_response.status != StatusCodes.OK:
        return None

    roblox_id = username_data.data[0].id if username_data.data else None

    return roblox_id


async def fetch_base_data(roblox_id: int) -> dict | None:
    """Fetch base data for a Roblox user."""

    user_base_data, user_base_data_response = await fetch_typed(
        RobloxUser,
        USERS_BASE_DATA_API.format(roblox_id=roblox_id),
        raise_on_failure=False
    )

    if user_base_data_response.status != StatusCodes.OK:
        return None

    return user_base_data.model_dump(exclude_unset=True)


async def fetch_user_groups(roblox_id: int) -> dict[Literal["groups"]: dict[int, RobloxUserGroups]] | None:
    """
    Fetch the groups of a user.

    This returns a dictionary with "groups" as the response
    so that this can be used with setattr() in the RobloxUser model.
    """

    user_groups, user_groups_response = await fetch_typed(
        RobloxUserGroupsResponse,
        USER_GROUPS_API.format(roblox_id=roblox_id),
        raise_on_failure=False
    )

    if user_groups_response.status != StatusCodes.OK:
        return None

    return {"groups": {int(group_data.group.id): group_data for group_data in user_groups.data}}


async def fetch_user_avatars(roblox_id: int, resolve_avatars: bool) -> dict[Literal["avatar"], UserAvatar]:
    """
    Fetch the avatar templates of a user.

    This returns a dictionary with "avatar" as the response
    so that this can be used with setattr() in the RobloxUser model.
    """

    avatars: dict = {}

    for avatar_name, avatar_url in AVATAR_URLS.items():
        if resolve_avatars:
            avatar_data, avatar_data_response = await fetch_typed(
                RobloxUserAvatarResponse,
                avatar_url.format(roblox_id=roblox_id),
                raise_on_failure=False
            )
            if avatar_data_response.status == StatusCodes.OK:
                avatars[avatar_name] = avatar_data.data[0].imageUrl
            else:
                avatars[avatar_name] = None
        else:
            avatars[avatar_name] = avatar_url.format(roblox_id=roblox_id)

    avatar_model = UserAvatar(**avatars)

    return {"avatar": avatar_model}


async def fetch_user_badges(roblox_id: int) -> list[RobloxUserBadge] | None:
    """
    Fetch the user's badges.

    This returns a dictionary with "badges" as the response
    so that this can be used with setattr() in the RobloxUser model.
    """

    user_badges, user_badges_response = await fetch_typed(
        RobloxUserBadgeResponse,
        USER_BADGES_API.format(roblox_id=roblox_id),
        raise_on_failure=False
    )

    if user_badges_response.status != StatusCodes.OK:
        return None

    return {"badges": user_badges.RobloxBadges}


async def get_user_account(
    user: hikari.User | MemberSerializable | str, guild_id: int = None, raise_errors=True
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

    user_id = str(user.id) if isinstance(
        user, (hikari.User, MemberSerializable)) else str(user)
    bloxlink_user = await fetch_user_data(user_id, "robloxID", "robloxAccounts")

    if guild_id:
        guild_accounts = (bloxlink_user.robloxAccounts or {}
                          ).get("guilds") or {}
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
    includes: list[Literal["groups", "badges"]] = None,
    *,
    roblox_username: str = None,
    roblox_id: int = None,
    guild_id: int = None,
) -> RobloxUser:
    """Get a Roblox account.

    If a user is not passed, it is required that either roblox_username OR roblox_id is given.

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
        RobloxUser | None: The found Roblox account, if any.
    """

    roblox_user: RobloxUser = None

    if roblox_id and roblox_username:
        raise ValueError(
            "You cannot provide both a roblox_id and a roblox_username.")

    if user and (roblox_username or roblox_id):
        raise ValueError(
            "You cannot provide both a user and a roblox_id or roblox_username.")

    if user:
        roblox_user = await get_user_account(user, guild_id)
        await roblox_user.sync(includes)

    else:
        roblox_user = RobloxUser(username=roblox_username, id=roblox_id)
        await roblox_user.sync(includes)

    return roblox_user


async def get_accounts(user_id: int) -> list[RobloxUser]:
    """Get a user's linked Roblox accounts.

    Args:
        user_id (int): The user to get linked Roblox accounts for.

    Returns:
        list[RobloxUser]: The linked Roblox accounts for this user.
    """

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


async def reverse_lookup(roblox_user: RobloxUser, exclude_user_id: int | None = None) -> list[int]:
    """Find Discord IDs linked to a roblox id.

    Args:
        roblox_user (RobloxUser): The roblox account that will be matched against.
        exclude_user_id (int | None, optional): Discord user ID that will not be included in the output.
            Defaults to None.

    Returns:
        list[int]: All the discord IDs linked to this roblox_id.
    """

    roblox_id = str(roblox_user.id)

    cursor = mongo.bloxlink["users"].find(
        {"$or": [{"robloxID": roblox_id}, {
            "robloxAccounts.accounts": roblox_id}]},
        {"_id": 1},
    )

    return [int(x["_id"]) async for x in cursor if str(exclude_user_id) != str(x["_id"])]


async def get_user_from_string(target: Annotated[str, "Roblox username or ID"]) -> RobloxUser:
    """Get a RobloxUser from a given target string (either an ID or username)

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
    if not account:
        try:
            account = await get_user(roblox_username=target)
        except RobloxNotFound as exc:
            raise RobloxNotFound(
                "The Roblox user you were searching for does not exist! "
                "Please check the input you gave and try again!"
            ) from exc

    if account.id is None or account.username is None:
        raise RobloxNotFound(
            "The Roblox user you were searching for does not exist.")

    return account


class MemberSerializable(BaseModel):
    id: Snowflake
    username: str = None
    avatar_url: str = None
    display_name: str = None
    global_name: str = None
    is_bot: bool = None
    joined_at: datetime = None
    role_ids: Sequence[Snowflake] = None
    guild_id: int | None = None
    nickname: str | None = None
    mention: str = None

    @classmethod
    def from_hikari(cls, member: hikari.InteractionMember | Self) -> 'MemberSerializable':
        """Convert a Hikari member into a MemberSerializable object."""

        if isinstance(member, MemberSerializable):
            return member

        return cls(
            id=member.id,
            username=member.username,
            avatar_url=str(member.avatar_url),
            global_name=member.global_name,
            display_name=member.display_name,
            is_bot=member.is_bot,
            joined_at=member.joined_at,
            role_ids=member.role_ids,
            guild_id=member.guild_id,
            nickname=member.nickname,
            mention=member.mention
        )

    @classmethod
    def from_discordpy(cls, member: discord.Member | Self) -> 'MemberSerializable':
        """Convert a Discord.py member into a MemberSerializable object."""

        if isinstance(member, MemberSerializable):
            return member

        return cls(
            id=member.id,
            username=member.name,
            avatar_url=member.display_avatar.url,
            global_name=member.global_name,
            display_name=member.display_name,
            is_bot=member.bot,
            joined_at=member.joined_at,
            role_ids=[role.id for role in member.roles],
            guild_id=member.guild.id,
            nickname=member.nick,
            mention=member.mention
        )
