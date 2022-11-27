"""The casambi integration."""
import asyncio
import logging
import ssl
import aiocasambi
import async_timeout

from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import aiohttp_client
from homeassistant.helpers.issue_registry import async_create_issue, IssueSeverity
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.const import (
    Platform,
    CONF_EMAIL,
    CONF_API_KEY,
    CONF_SCAN_INTERVAL,
)

from .const import (
    DOMAIN,
    CONF_CONTROLLER,
    CONF_USER_PASSWORD,
    CONF_NETWORK_PASSWORD,
    CONF_NETWORK_TIMEOUT,
    DEFAULT_NETWORK_TIMEOUT,
    DEFAULT_POLLING_TIME,
    MAX_START_UP_TIME,
)

from .errors import ConfigurationError
from .casambi.CasambiController import CasambiController

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, config_entry: ConfigEntry
) -> bool:
    """Set up platform from a ConfigEntry."""
    hass.data.setdefault(DOMAIN, {})

    config = hass.data[DOMAIN][config_entry.entry_id] = dict(config_entry.data)
    # Registers update listener to update config entry when options are updated.
    # Store a reference to the unsubscribe function to cleanup if an entry is unloaded.
    config["remove_update_listener"] = config_entry.add_update_listener(options_update_listener)

    user_password = None
    if CONF_USER_PASSWORD in config:
        user_password = config[CONF_USER_PASSWORD]
    if user_password == "":
        user_password = None

    network_password = None
    if CONF_NETWORK_PASSWORD in config:
        network_password = config[CONF_NETWORK_PASSWORD]
    if network_password == "":
        network_password = None

    email = config[CONF_EMAIL]

    api_key = config[CONF_API_KEY]

    network_timeout = DEFAULT_NETWORK_TIMEOUT
    if CONF_NETWORK_TIMEOUT in config:
        network_timeout = config[CONF_NETWORK_TIMEOUT]

    scan_interval = DEFAULT_POLLING_TIME
    if CONF_SCAN_INTERVAL in config:
        scan_interval = config[CONF_SCAN_INTERVAL]

    if CONF_CONTROLLER in hass.data[DOMAIN]:
        dbg_msg = "async_setup_platform CasambiController already created!"
        _LOGGER.debug(dbg_msg)

        async_create_issue(
            hass=hass,
            domain=DOMAIN,
            issue_id="restart_required_casambi",
            is_fixable=True,
            issue_domain=DOMAIN,
            severity=IssueSeverity.WARNING,
            translation_key="restart_required",
            translation_placeholders={},
        )
        return True

    casambi_controller = hass.data[DOMAIN][CONF_CONTROLLER] = CasambiController(hass)

    if not (user_password) and not (network_password):
        err_msg = f"{CONF_USER_PASSWORD} or {CONF_NETWORK_PASSWORD} "
        err_msg += "must be set in config!"

        raise ConfigurationError(err_msg)

    casambi_controller.controller = aiocasambi.Controller(
        email=email,
        user_password=user_password,
        network_password=network_password,
        api_key=api_key,
        websession=aiohttp_client.async_get_clientsession(hass),
        sslcontext=ssl.create_default_context(),
        callback=casambi_controller.signalling_callback,
        network_timeout=network_timeout,
    )

    try:
        with async_timeout.timeout(MAX_START_UP_TIME):
            await casambi_controller.controller.create_session()
            await casambi_controller.controller.initialize()
            await casambi_controller.controller.start_websockets()

    except aiocasambi.LoginRequired:
        _LOGGER.error("Integrations UI setup: Connected to casambi but couldn't log in")
        return False

    except aiocasambi.Unauthorized:
        _LOGGER.error("Integrations UI setup: Connected to casambi but not registered")
        return False

    except aiocasambi.RequestError as err:
        _LOGGER.error(
            f"Integrations UI setup: Error connecting to the Casambi, caught aiocasambi.RequestError, error message: {str(err)}"
        )
        return False

    except asyncio.TimeoutError:
        _LOGGER.error(
            "Integrations UI setup: Error connecting to the Casambi, caught asyncio.TimeoutError"
        )
        return False

    except aiocasambi.AiocasambiException:
        _LOGGER.error(
            "Integrations UI setup: Unknown Casambi communication error occurred!"
        )
        return False

    hass.data[DOMAIN]["coordinator"] = DataUpdateCoordinator(
        hass,
        _LOGGER,
        # Name of the data. For logging purposes.
        name="light",
        update_method=casambi_controller.async_update_data,
        # Polling interval. Will only be polled if there are subscribers.
        update_interval=timedelta(seconds=scan_interval),
    )

    # Forward the setup to the sensor platform.
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(config_entry, Platform.LIGHT)
    )

    return True


async def options_update_listener(hass: HomeAssistant, config_entry: ConfigEntry):
    """Handle options update."""
    await hass.config_entries.async_reload(config_entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[hass.config_entries.async_forward_entry_unload(entry, Platform.LIGHT)]
        )
    )
    # Remove options_update_listener.
    hass.data[DOMAIN][entry.entry_id]["remove_update_listener"]()

    # Remove config entry from domain.
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_setup(hass: HomeAssistant, config: ConfigEntry) -> bool:
    """Set up the GitHub Custom component from yaml configuration."""
    hass.data.setdefault(DOMAIN, {})
    return True
