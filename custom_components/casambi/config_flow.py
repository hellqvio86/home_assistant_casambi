from copy import deepcopy
import logging
from typing import Any, Dict, Optional

from homeassistant import config_entries, core
from homeassistant.const import (
    CONF_ACCESS_TOKEN,
    CONF_NAME,
    CONF_EMAIL,
    CONF_API_KEY,
    CONF_PATH,
    CONF_URL,
    CONF_SCAN_INTERVAL
)
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity_registry import (
    async_entries_for_config_entry,
    async_get_registry,
)
import voluptuous as vol

from .const import (
    DOMAIN,
    WIRE_ID,
    CONFIG_SCHEMA,
    CONF_USER_PASSWORD,
    CONF_NETWORK_PASSWORD,
    CONF_NETWORK_TIMEOUT,
    ATTR_IDENTIFIERS,
    ATTR_MANUFACTURER,
    ATTR_MODEL,
)

_LOGGER = logging.getLogger(__name__)

CONF_REPOS = 'FOOBAR'
AUTH_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_EMAIL): cv.string,
        vol.Required(CONF_API_KEY): cv.string,
        vol.Required(CONF_USER_PASSWORD): cv.string,
        vol.Required(CONF_NETWORK_PASSWORD): cv.string
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

async def validate_auth(email: str, api_key: str, user_password: str, 
    network_password: str, hass: core.HomeAssistant) -> None:
    """Validates a GitHub access token.

    Raises a ValueError if the auth token is invalid.
    """
    session = async_get_clientsession(hass)


class CasambiConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Github Custom config flow."""

    data: Optional[Dict[str, Any]]

    async def async_step_user(self, user_input: Optional[Dict[str, Any]] = None):
        """Invoked when a user initiates a flow via the user interface."""
        errors: Dict[str, str] = {}
        if user_input is not None:
            _LOGGER.debug(f"async_step_user user_input: {user_input}")
            try:
                await validate_auth(user_input[CONF_EMAIL], user_input[CONF_API_KEY], user_input[CONF_USER_PASSWORD], user_input[CONF_NETWORK_PASSWORD], self.hass)
            except ValueError:
                errors["base"] = "auth"
            if not errors:
                # Input is valid, set data.
                self.data = user_input

                # Return the form of the next step.
                return self.async_create_entry(title="Casambi", data=self.data)

        return self.async_show_form(
            step_id="user", data_schema=AUTH_SCHEMA, errors=errors
        )
