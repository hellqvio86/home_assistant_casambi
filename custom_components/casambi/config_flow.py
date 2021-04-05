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


async def validate_path(path: str, access_token: str, hass: core.HassJob) -> None:
    """Validates a GitHub repo path.

    Raises a ValueError if the path is invalid.
    """
    if len(path.split("/")) != 2:
        raise ValueError
    session = async_get_clientsession(hass)


async def validate_auth(access_token: str, hass: core.HomeAssistant) -> None:
    """Validates a GitHub access token.

    Raises a ValueError if the auth token is invalid.
    """
    session = async_get_clientsession(hass)


class GithubCustomConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Github Custom config flow."""

    data: Optional[Dict[str, Any]]

    async def async_step_user(self, user_input: Optional[Dict[str, Any]] = None):
        """Invoked when a user initiates a flow via the user interface."""
        errors: Dict[str, str] = {}
        if user_input is not None:
            try:
                await validate_auth(user_input[CONF_ACCESS_TOKEN], self.hass)
            except ValueError:
                errors["base"] = "auth"
            if not errors:
                # Input is valid, set data.
                self.data = user_input
                self.data[CONF_REPOS] = []
                # Return the form of the next step.
                return await self.async_step_repo()

        return self.async_show_form(
            step_id="user", data_schema=AUTH_SCHEMA, errors=errors
        )

    async def async_step_repo(self, user_input: Optional[Dict[str, Any]] = None):
        """Second step in config flow to add a repo to watch."""
        errors: Dict[str, str] = {}
        if user_input is not None:
            # Validate the path.
            try:
                await validate_path(
                    user_input[CONF_PATH], self.data[CONF_ACCESS_TOKEN], self.hass
                )
            except ValueError:
                errors["base"] = "invalid_path"

            if not errors:
                # Input is valid, set data.
                self.data[CONF_REPOS].append(
                    {
                        "path": user_input[CONF_PATH],
                        "name": user_input.get(CONF_NAME, user_input[CONF_PATH]),
                    }
                )
                # If user ticked the box show this form again so they can add an
                # additional repo.
                if user_input.get("add_another", False):
                    return await self.async_step_repo()

                # User is done adding repos, create the config entry.
                return self.async_create_entry(title="GitHub Custom", data=self.data)

        return self.async_show_form(
            step_id="repo", data_schema=REPO_SCHEMA, errors=errors
        )
