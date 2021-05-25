"""Constants for the casambi integration."""
import voluptuous as vol
import homeassistant.helpers.config_validation as cv

from homeassistant.const import (
    CONF_EMAIL,
    CONF_API_KEY,
    CONF_SCAN_INTERVAL
)

DOMAIN = "casambi"

WIRE_ID = 9

DEFAULT_NETWORK_TIMEOUT = 300
DEFAULT_POLLING_TIME = 60

CONF_USER_PASSWORD = "user_password"
CONF_NETWORK_PASSWORD = "network_password"
CONF_NETWORK_TIMEOUT = 'network_timeout'
CONF_CONTROLLER = 'controller'

ATTR_IDENTIFIERS = "identifiers"
ATTR_MANUFACTURER = "manufacturer"
ATTR_MODEL = "model"
ATTR_SOFTWARE_VERSION = "sw_version"

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_USER_PASSWORD): cv.string,
        vol.Required(CONF_NETWORK_PASSWORD): cv.string,
        vol.Required(CONF_EMAIL): cv.string,
        vol.Required(CONF_API_KEY): cv.string,
        vol.Optional(CONF_NETWORK_TIMEOUT, default=DEFAULT_NETWORK_TIMEOUT): cv.positive_int,
        vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_POLLING_TIME): cv.positive_int,
    })
}, extra=vol.ALLOW_EXTRA)
