class BloxlinkException(Exception):
    """Base exception for Bloxlink."""

    def __init__(self, message=None, ephemeral=False):
        self.message = message
        self.ephemeral = ephemeral

class RobloxNotFound(BloxlinkException):
    """Raised when a Roblox entity is not found."""

class RobloxAPIError(BloxlinkException):
    """Raised when the Roblox API returns an error."""

class RobloxDown(BloxlinkException):
    """Raised when the Roblox API is down."""
