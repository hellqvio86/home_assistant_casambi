import logging
import voluptuous as vol
import homeassistant.helpers.config_validation as cv


from aiocasambi import helper
from aiocasambi.errors import AiocasambiException
from homeassistant import config_entries
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


async def validate_auth(email: str, api_key: str, user_password: str, \
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

    async def async_step_user(self, info):
        if info is not None:
            _LOGGER.debug(f"info is: {info}")
            pass  # TODO: process info

        return self.async_show_form(
            step_id="user", data_schema=vol.Schema({
                DOMAIN: vol.Schema({
                    vol.Required(CONF_USER_PASSWORD): cv.string,
                    vol.Required(CONF_NETWORK_PASSWORD): cv.string,
                    vol.Required(CONF_EMAIL): cv.string,
                    vol.Required(CONF_API_KEY): cv.string,
                    vol.Required(CONF_NETWORK_TIMEOUT, default=300): cv.positive_int,
                    vol.Required(CONF_SCAN_INTERVAL, default=60): cv.positive_int,
                })
            }, extra=vol.ALLOW_EXTRA)
        )
