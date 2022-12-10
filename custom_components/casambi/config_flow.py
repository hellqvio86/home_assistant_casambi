"""
Config flow for Casambi integration
"""
import logging
from typing import Any, Dict, Optional

import homeassistant.helpers.config_validation as cv
from homeassistant import config_entries, core
from homeassistant.const import (
    CONF_NAME,
    CONF_EMAIL,
    CONF_API_KEY,
)
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import voluptuous as vol

from aiocasambi.helper import Helper
from aiocasambi.errors import AiocasambiException

from .const import (
    DOMAIN,
    CONF_USER_PASSWORD,
    CONF_NETWORK_PASSWORD,
)

_LOGGER = logging.getLogger(__name__)

AUTH_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_EMAIL): cv.string,
        vol.Required(CONF_API_KEY): cv.string,
        vol.Required(CONF_USER_PASSWORD): cv.string,
        vol.Required(CONF_NETWORK_PASSWORD): cv.string,
    }
)
REPO_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USER_PASSWORD): cv.string,
        vol.Optional(CONF_NAME): cv.string,
        vol.Optional("add_another"): cv.boolean,
    }
)

OPTIONS_SHCEMA = vol.Schema({vol.Optional(CONF_NAME, default="foo"): cv.string})


async def validate_user_password(
    email: str, api_key: str, user_password: str, hass: core.HomeAssistant
) -> None:
    """
    Validates a GitHub access token.

    Raises a ValueError if the auth token is invalid.
    """
    session = async_get_clientsession(hass)
    helper = Helper(email=email, api_key=api_key, websession=session)

    try:
        await helper.test_user_password(password=user_password)
    except AiocasambiException:
        raise ValueError


async def validate_network_password(
    email: str, api_key: str, network_password: str, hass: core.HomeAssistant
) -> None:
    """
    Validates a GitHub access token.

    Raises a ValueError if the auth token is invalid.
    """
    session = async_get_clientsession(hass)
    helper = Helper(email=email, api_key=api_key, websession=session)

    try:
        await helper.test_network_password(password=network_password)
    except AiocasambiException:
        raise ValueError


class CasambiConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """
    Github Custom config flow.
    """

    data: Optional[Dict[str, Any]] = {}

    async def async_step_user(self, user_input: Optional[Dict[str, Any]] = None):
        """Invoked when a user initiates a flow via the user interface."""
        errors: Dict[str, str] = {}
        if user_input is not None:
            _LOGGER.debug(f"async_step_user user_input: {user_input}")
            self.data[CONF_API_KEY] = user_input[CONF_API_KEY]

            # Return the form of the next step.
            return await self.async_step_site_user()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_API_KEY): cv.string,
                }
            ),
            errors=errors,
            last_step=False,
        )

    async def async_step_site_user(self, user_input: Optional[Dict[str, Any]] = None):
        """
        Invoked when a user has provided the API key via the user interface.
        """
        errors: Dict[str, str] = {}

        if user_input is not None:
            _LOGGER.debug(f"async_step_site_user user_input: {user_input}")
            try:
                await validate_user_password(
                    user_input[CONF_EMAIL],
                    self.data[CONF_API_KEY],
                    user_input[CONF_USER_PASSWORD],
                    self.hass,
                )
            except ValueError:
                errors["base"] = "auth_user_password"

            if not errors:
                self.data[CONF_EMAIL] = user_input[CONF_EMAIL]
                self.data[CONF_USER_PASSWORD] = user_input[CONF_USER_PASSWORD]
                # Return the form of the next step.
                return await self.async_step_network()

        return self.async_show_form(
            step_id="site_user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_EMAIL): cv.string,
                    vol.Required(CONF_USER_PASSWORD): cv.string,
                }
            ),
            errors=errors,
            last_step=False,
        )

    async def async_step_network(self, user_input: Optional[Dict[str, Any]] = None):
        """
        Invoked when a user has provided the API key and site credentials via the user interface.
        """
        errors: Dict[str, str] = {}

        if user_input is not None:
            _LOGGER.debug(f"async_step_network user_input: {user_input}")
            try:
                await validate_network_password(
                    self.data[CONF_EMAIL],
                    self.data[CONF_API_KEY],
                    user_input[CONF_NETWORK_PASSWORD],
                    self.hass,
                )
            except ValueError:
                errors["base"] = "auth_network_password"

            if not errors:
                self.data[CONF_NETWORK_PASSWORD] = user_input[CONF_NETWORK_PASSWORD]
                # Return the form of the next step.
                return self.async_create_entry(title="Casambi", data=self.data)

        return self.async_show_form(
            step_id="network",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_NETWORK_PASSWORD): cv.string,
                }
            ),
            errors=errors,
            last_step=True,
        )
