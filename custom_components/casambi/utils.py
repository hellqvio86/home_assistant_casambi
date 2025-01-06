"""
Utils for Casambi
"""

import logging
import ssl
import asyncio

from datetime import timedelta

import aiocasambi

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers import aiohttp_client

from homeassistant.const import (
    CONF_EMAIL,
    CONF_API_KEY,
    CONF_SCAN_INTERVAL,
)

from .casambi.CasambiController import CasambiController
from .errors import ConfigurationError

from .const import (
    CONF_USER_PASSWORD,
    CONF_NETWORK_PASSWORD,
    CONF_NETWORK_TIMEOUT,
    DEFAULT_NETWORK_TIMEOUT,
    DEFAULT_POLLING_TIME,
)

_LOGGER = logging.getLogger(__name__)


async def async_create_ssl_context(hass: HomeAssistant):
    """
    Create SSL context in an executor to avoid blocking the event loop.
    """
    return await hass.async_add_executor_job(ssl.create_default_context)


async def async_create_controller(
    hass: HomeAssistant, config: ConfigEntry
) -> CasambiController:
    """
    Creates a Controller for the Casambi API.
    """
    api_key = config[CONF_API_KEY]

    email = config[CONF_EMAIL]

    ssl_context = await async_create_ssl_context(hass)

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

    network_timeout = DEFAULT_NETWORK_TIMEOUT
    if CONF_NETWORK_TIMEOUT in config:
        network_timeout = config[CONF_NETWORK_TIMEOUT]

    if not user_password and not network_password:
        err_msg = f"{CONF_USER_PASSWORD} or {CONF_NETWORK_PASSWORD} "
        err_msg += "must be set in config!"
        raise ConfigurationError(err_msg)

    controller = CasambiController(hass)

    aiocasambi_controller = controller.aiocasambi_controller = aiocasambi.Controller(
        email=email,
        user_password=user_password,
        network_password=network_password,
        api_key=api_key,
        websession=aiohttp_client.async_get_clientsession(hass),
        sslcontext=ssl_context,
        callback=controller.signalling_callback,
        network_timeout=network_timeout,
    )

    try:
        await aiocasambi_controller.create_session()
        await aiocasambi_controller.initialize()
        await aiocasambi_controller.start_websockets()

    except aiocasambi.Unauthorized:
        _LOGGER.error("Connected to casambi but couldn't log in")
        return None

    except asyncio.TimeoutError:
        err_msg = "Error connecting to the Casambi, "
        err_msg += "caught asyncio.TimeoutError"
        _LOGGER.error(err_msg)
        return None

    except aiocasambi.AiocasambiException as err:
        err_msg = "Unknown Casambi communication error occurred! "
        err_msg += f"err: {err}"
        _LOGGER.error(err_msg)
        return None

    # Sleep so we get some websocket messages,
    # oem and other settings needs to be set
    # await asyncio.sleep(2)

    return controller


async def async_create_coordinator(
    hass: HomeAssistant,
    config: ConfigEntry,
    controller: CasambiController,
) -> DataUpdateCoordinator:
    """Creates an Update Coordinator."""
    scan_interval = DEFAULT_POLLING_TIME
    if CONF_SCAN_INTERVAL in config:
        scan_interval = config[CONF_SCAN_INTERVAL]

    _LOGGER.debug(
        f"Creating coordinator with scan_interval: {scan_interval} hass: {hass} config: {config} controller: {controller}"
    )

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        # Name of the data. For logging purposes.
        name="light",
        update_method=controller.async_update_data,
        # Polling interval. Will only be polled if there are subscribers.
        update_interval=timedelta(seconds=scan_interval),
    )

    await coordinator.async_refresh()

    return coordinator
