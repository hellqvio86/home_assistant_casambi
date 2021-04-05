import logging
import voluptuous as vol
import homeassistant.helpers.config_validation as cv

from typing import Any, Dict, Optional
from aiocasambi import helper
from aiocasambi.errors import AiocasambiException
from homeassistant import config_entries, core
from homeassistant.const import (
    CONF_EMAIL,
    CONF_API_KEY,
    CONF_SCAN_INTERVAL
)

from .const import (
    DOMAIN,
    CONF_USER_PASSWORD,
    CONF_NETWORK_PASSWORD,
    CONF_NETWORK_TIMEOUT
)

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_USER_PASSWORD): cv.string,
        vol.Required(CONF_NETWORK_PASSWORD): cv.string,
        vol.Required(CONF_EMAIL): cv.string,
        vol.Required(CONF_API_KEY): cv.string,
        vol.Required(CONF_NETWORK_TIMEOUT, default=300): cv.positive_int,
        vol.Required(CONF_SCAN_INTERVAL, default=60): cv.positive_int,
    })
}, extra=vol.ALLOW_EXTRA)


async def validate_auth(email: str, api_key: str, user_password: str,
                        network_password: str, hass: core.HomeAssistant) -> None:
    """ Validates a Casambi credentials.

    Raises a if credentials is invalid
    """
    worker = helper.Helper(email=email, api_key=api_key)

    try:
        await worker.test_user_password(password=user_password)
    except AiocasambiException:
        raise ValueError

    try:
        await worker.test_network_password(password=network_password)
    except AiocasambiException:
        raise ValueError


class CasambiFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle Casambi config flow"""

    VERSION = 1

    data: Optional[Dict[str, Any]]

    async def async_step_user(self, user_input: Optional[Dict[str, Any]] = None):
        errors: Dict[str, str] = {}

        if user_input is not None:
            try:
                await validate_auth(user_input[CONF_EMAIL],
                                    user_input[CONF_API_KEY],
                                    user_input[CONF_USER_PASSWORD],
                                    user_input[CONF_NETWORK_PASSWORD],
                                    self.hass)
            except ValueError:
                errors["base"] = "auth"
            if not errors:
                # Input is valid, set data.
                self.data = user_input

                # User is done adding repos, create the config entry.
                return self.async_create_entry(title="Casambi", data=self.data)
        return self.async_show_form(
            step_id="user", data_schema=CONFIG_SCHEMA)
