"""Errors for the Casambi component."""
from homeassistant.exceptions import HomeAssistantError


class CasambiException(HomeAssistantError):
    """Base class for Casambi exceptions."""


class ConfigurationError(CasambiException):
    """Invalid configuration"""
