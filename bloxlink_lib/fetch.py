import asyncio
import logging
from enum import IntEnum
from typing import Literal, Type, Union, Tuple
from aiohttp import ClientResponse
from pydantic import BaseModel
import aiohttp
from requests.utils import requote_uri

from .exceptions import RobloxAPIError, RobloxDown, RobloxNotFound
from .config import CONFIG

__all__ = ("fetch", "StatusCodes")


session = None

class StatusCodes(IntEnum):
    """Status codes for requests"""

    OK = 200
    NOT_FOUND = 404
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    TOO_MANY_REQUESTS = 429
    INTERNAL_SERVER_ERROR = 500
    SERVICE_UNAVAILABLE = 503
    GATEWAY_TIMEOUT = 504


async def fetch[T](
    method: str,
    url: str,
    *,
    params: dict[str, str] = None,
    headers: dict = None,
    body: dict = None,
    parse_as: Literal["JSON", "BYTES", "TEXT"] | BaseModel | Type[T] = "JSON",
    raise_on_failure: bool = True,
    timeout: float = 10,
) -> Union[Tuple[dict, ClientResponse], Tuple[str, ClientResponse], Tuple[bytes, ClientResponse], Tuple[T, ClientResponse], ClientResponse]:
    """Make a REST request with the ability to proxy.

    Only Roblox URLs are proxied, all other requests to other domains are sent as is.

    Args:
        method (str): The HTTP request method to use for this query.
        url (str): The URL to send the request to.
        params (dict, optional): Query parameters to append to the URL. Defaults to None.
        headers (dict, optional): Headers to use when sending the request. Defaults to None.
        body (dict, optional): Data to pass in the body of the request. Defaults to None.
        parse_as (JSON | BYTES | TEXT | Type[T], optional): Set what the expected type to return should be.
            Defaults to JSON.
        raise_on_failure (bool, optional): Whether an exception be raised if the request fails. Defaults to True.
        timeout (float, optional): How long should we wait for a request to succeed. Defaults to 10 seconds.

    Raises:
        RobloxAPIError:
            For proxied requests, raised when the proxy server returns a data format that is not JSON.
            When a request returns a status code that is NOT 503 or 404, but is over 400 (if raise_on_failure).
            When a non-proxied request does not match the expected data type (typically JSON).
        RobloxDown: Raised if raise_on_failure, and the status code is 503. Also raised on request timeout.
        RobloxNotFound: Raised if raise_on_failure, and the status code is 404.

    Returns:
        Tuple[dict, ClientResponse] | Tuple[str, ClientResponse] | Tuple[bytes, ClientResponse] | ClientResponse:
        The requested data from the request, if any.
    """
    global session  # pylint: disable=global-statement

    params = params or {}
    headers = headers or {}

    if not session:
        session = aiohttp.ClientSession()

    url = requote_uri(url)

    for k, v in params.items():
        if isinstance(v, bool):
            params[k] = "true" if v else "false"

    try:
        async with session.request(
            method,
            url,
            json=body,
            params=params,
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=timeout) if timeout else None,
            proxy=CONFIG.PROXY_URL if CONFIG.PROXY_URL and "roblox.com" in url else None,
        ) as response:
            if response.status != StatusCodes.OK and raise_on_failure:
                if response.status == StatusCodes.SERVICE_UNAVAILABLE:
                    raise RobloxDown()

                if response.status == StatusCodes.NOT_FOUND:
                    raise RobloxNotFound()

                raise RobloxAPIError(f"{url} failed with status {response.status} and body {await response.text()}")

            if parse_as:
                if parse_as == "TEXT":
                    return await response.text(), response

                if parse_as == "JSON":
                    try:
                        json_response = await response.json()
                    except aiohttp.client_exceptions.ContentTypeError as exc:
                        logging.debug(f"{url} {await response.text()}")

                        raise RobloxAPIError() from exc

                    return json_response, response

                if parse_as == "BYTES":
                    return await response.read(), response

                if isinstance(parse_as, BaseModel):
                    json_response = await response.json()
                    # Filter only relevant fields before constructing the pydantic instance
                    relevant_fields = {field_name: json_response[field_name] for field_name in parse_as.model_fields.keys() if field_name in json_response}
                    return parse_as(**relevant_fields), response

                if isinstance(parse_as, dict):
                    json_response = await response.json()
                    return {key: json_response[value] for key, value in parse_as.items()}, response

            return response

    except asyncio.TimeoutError:
        logging.debug(f"URL {url} timed out")
        raise RobloxDown() from None

async def fetch_typed[T](url: str, parse_as: Type[T], method="GET", **kwargs) -> Tuple[T, ClientResponse]:
    """Fetch data from a URL and parse it as a dataclass.

    Args:
        url (str): The URL to send the request to.
        parse_as (Type[T]): The dataclass to parse the response as.

    Returns:
        T: The dataclass instance of the response.
    """
    return await fetch(url=url, parse_as=parse_as, method=method, **kwargs)
