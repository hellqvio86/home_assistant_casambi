"""Errors for the Casambi component."""
from homeassistant.exceptions import HomeAssistantError


class CasambiException(HomeAssistantError):
    """Base class for Casambi exceptions."""


class AlreadyConfigured(CasambiException):
    """Controller is already configured."""


class AuthenticationRequired(CasambiException):
    """Unknown error occurred."""


class CannotConnect(CasambiException):
    """Unable to connect to the controller."""


class LoginRequired(CasambiException):
    """Component got logged out."""


class UserLevel(CasambiException):
    """User level too low."""


class InvalidCredentials(CasambiException):
    """User invalid credentials."""
