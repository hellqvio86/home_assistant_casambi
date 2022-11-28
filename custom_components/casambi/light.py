"""
Support for Casambi lights.
For more details about this component, please refer to the documentation at
https://home-assistant.io/components/@todo
"""
import logging
import ssl
import asyncio

from datetime import timedelta

import async_timeout
import aiocasambi

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
)

try:
    from homeassistant.components.light import ATTR_DISTRIBUTION
except ImportError:
    ATTR_DISTRIBUTION = "distribution"

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.helpers import aiohttp_client, entity_platform
from homeassistant.helpers.issue_registry import async_create_issue, IssueSeverity
from homeassistant.const import CONF_EMAIL, CONF_API_KEY, CONF_SCAN_INTERVAL

import voluptuous as vol

from .const import (
    DOMAIN,
    CONF_CONTROLLER,
    CONF_USER_PASSWORD,
    CONF_NETWORK_PASSWORD,
    CONF_NETWORK_TIMEOUT,
    DEFAULT_NETWORK_TIMEOUT,
    DEFAULT_POLLING_TIME,
    SERVICE_CASAMBI_LIGHT_TURN_ON,
    MAX_START_UP_TIME,
    ATTR_SERV_BRIGHTNESS,
    ATTR_SERV_DISTRIBUTION,
    ATTR_SERV_ENTITY_ID,
)

from .errors import ConfigurationError
from .casambi.CasambiLightEntity import CasambiLightEntity
from .casambi.CasambiController import CasambiController

_LOGGER = logging.getLogger(__name__)

CASAMBI_CONTROLLER = None


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities,
):
    """Setup sensors from a config entry created in the integrations UI."""
    config = hass.data[DOMAIN][config_entry.entry_id]
    user_password = None
    if CONF_USER_PASSWORD in config:
        user_password = config[CONF_USER_PASSWORD]
    network_password = None
    if CONF_NETWORK_PASSWORD in config:
        network_password = config[CONF_NETWORK_PASSWORD]
    email = config[CONF_EMAIL]
    api_key = config[CONF_API_KEY]

    network_timeout = DEFAULT_NETWORK_TIMEOUT
    scan_interval = DEFAULT_POLLING_TIME

    if CONF_NETWORK_TIMEOUT in config:
        network_timeout = config[CONF_NETWORK_TIMEOUT]

    if CONF_SCAN_INTERVAL in config:
        scan_interval = config[CONF_SCAN_INTERVAL]

    sslcontext = ssl.create_default_context()
    session = aiohttp_client.async_get_clientsession(hass)

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

    hass.data[DOMAIN][CONF_CONTROLLER] = CasambiController(hass)
    casambi_controller = hass.data[DOMAIN][CONF_CONTROLLER]

    if user_password == "":
        user_password = None

    if network_password == "":
        network_password = None

    if not user_password and not network_password:
        err_msg = f"{CONF_USER_PASSWORD} or {CONF_NETWORK_PASSWORD} "
        err_msg += "must be set in config!"

        raise ConfigurationError(err_msg)

    aiocasambi_controller = aiocasambi.Controller(
        email=email,
        user_password=user_password,
        network_password=network_password,
        api_key=api_key,
        websession=session,
        sslcontext=sslcontext,
        callback=casambi_controller.signalling_callback,
        network_timeout=network_timeout,
    )

    casambi_controller.aiocasambi_controller = aiocasambi_controller

    try:
        with async_timeout.timeout(MAX_START_UP_TIME):
            await aiocasambi_controller.create_session()
            await aiocasambi_controller.initialize()
            await aiocasambi_controller.start_websockets()

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

    units = aiocasambi_controller.get_units()

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        # Name of the data. For logging purposes.
        name="light",
        update_method=casambi_controller.async_update_data,
        # Polling interval. Will only be polled if there are subscribers.
        update_interval=timedelta(seconds=scan_interval),
    )

    await coordinator.async_refresh()

    for unit in units:
        if not unit.is_light():
            continue

        casambi_light = CasambiLightEntity(
            coordinator, unit.unique_id, unit, aiocasambi_controller, hass
        )
        async_add_entities([casambi_light], True)

        casambi_controller.lights[casambi_light.unique_id] = casambi_light

    # add entity service to turn on Casambi light
    platform = entity_platform.async_get_current_platform()
    platform.async_register_entity_service(
        SERVICE_CASAMBI_LIGHT_TURN_ON,
        {
            vol.Required(ATTR_BRIGHTNESS): vol.All(
                vol.Coerce(int), vol.Range(min=0, max=255)
            ),
            vol.Optional(ATTR_DISTRIBUTION): vol.All(
                vol.Coerce(int), vol.Range(min=0, max=255)
            ),
        },
        "async_handle_entity_service_light_turn_on",
    )

    return True


async def async_setup_platform(
    hass: HomeAssistant, config: dict, async_add_entities, discovery_info=None
):
    """
    Setup Casambi platform, called when setup through configuration.yaml
    """
    user_password = None
    if CONF_USER_PASSWORD in config:
        user_password = config[CONF_USER_PASSWORD]
    network_password = None
    if CONF_NETWORK_PASSWORD in config:
        network_password = config[CONF_NETWORK_PASSWORD]
    email = config[CONF_EMAIL]
    api_key = config[CONF_API_KEY]

    network_timeout = DEFAULT_NETWORK_TIMEOUT
    scan_interval = DEFAULT_POLLING_TIME

    if CONF_NETWORK_TIMEOUT in config:
        network_timeout = config[CONF_NETWORK_TIMEOUT]

    if CONF_SCAN_INTERVAL in config:
        scan_interval = config[CONF_SCAN_INTERVAL]

    sslcontext = ssl.create_default_context()
    session = aiohttp_client.async_get_clientsession(hass)

    if CONF_CONTROLLER in hass.data[DOMAIN]:
        dbg_msg = "async_setup_platform CasambiController already created!"
        _LOGGER.debug(dbg_msg)
        return

    hass.data[DOMAIN][CONF_CONTROLLER] = CasambiController(hass)
    casambi_controller = hass.data[DOMAIN][CONF_CONTROLLER]

    if user_password == "":
        user_password = None

    if network_password == "":
        network_password = None

    if not user_password and not network_password:
        raise ConfigurationError(
            f"{CONF_USER_PASSWORD} or {CONF_NETWORK_PASSWORD} must be set in config!"
        )

    aiocasambi_controller = aiocasambi.Controller(
        email=email,
        user_password=user_password,
        network_password=network_password,
        api_key=api_key,
        websession=session,
        sslcontext=sslcontext,
        callback=casambi_controller.signalling_callback,
        network_timeout=network_timeout,
    )

    casambi_controller.aiocasambi_controller = aiocasambi_controller

    try:
        with async_timeout.timeout(MAX_START_UP_TIME):
            await aiocasambi_controller.create_session()
            await aiocasambi_controller.initialize()
            await aiocasambi_controller.start_websockets()

    except aiocasambi.LoginRequired:
        _LOGGER.error(
            "configuration.yaml setup: Connected to casambi but couldn't log in"
        )
        return False

    except aiocasambi.Unauthorized:
        _LOGGER.error(
            "configuration.yaml setup: Connected to casambi but not registered"
        )
        return False

    except aiocasambi.RequestError as err:
        _LOGGER.error(
            f"configuration.yaml setup: Error connecting to the Casambi, caught aiocasambi.RequestError, error message: {str(err)}"
        )
        return False

    except asyncio.TimeoutError:
        _LOGGER.error(
            "configuration.yaml setup: Error connecting to the Casambi, caught asyncio.TimeoutError"
        )
        return False

    except aiocasambi.AiocasambiException:
        _LOGGER.error(
            "configuration.yaml setup: Unknown Casambi communication error occurred!"
        )
        return False

    units = aiocasambi_controller.get_units()

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        # Name of the data. For logging purposes.
        name="light",
        update_method=casambi_controller.async_update_data,
        # Polling interval. Will only be polled if there are subscribers.
        update_interval=timedelta(seconds=scan_interval),
    )

    await coordinator.async_refresh()

    for unit in units:
        if not unit.is_light():
            continue

        casambi_light = CasambiLightEntity(
            coordinator, unit.unique_id, unit, aiocasambi_controller, hass
        )
        async_add_entities([casambi_light], True)

        casambi_controller.lights[casambi_light.unique_id] = casambi_light

    @callback
    async def async_handle_platform_service_light_turn_on(call: ServiceCall) -> None:
        """Handle turn on of Casambi light when setup from yaml."""
        dbg_msg = f"ServiceCall {call.domain}.{call.service}, "
        dbg_msg += "data: {call.data}"
        _LOGGER.debug(dbg_msg)

        # Check if entities were selected
        if ATTR_SERV_ENTITY_ID not in call.data:
            # service handle currently only supports selection of entities
            dbg_msg = f"ServiceCall {call.domain}.{call.service}:"
            dbg_msg += " No entity was specified."
            dbg_msg += " Please specify entities instead of areas or devices."
            _LOGGER.error(dbg_msg)

            return

        # Get parameters
        _distribution = None
        _brightness = call.data[ATTR_SERV_BRIGHTNESS]
        _entity_ids = call.data[ATTR_SERV_ENTITY_ID]

        dbg_msg = f"ServiceCall {call.domain}.{call.service}:"
        dbg_msg += f" data: {call.data}, brightness: {_brightness},"
        dbg_msg += f" entity_ids: {_entity_ids}"

        # Check if optional attribute distribution has been set
        if ATTR_SERV_DISTRIBUTION in call.data:
            _distribution = call.data[ATTR_SERV_DISTRIBUTION]
            dbg_msg += f", distribution: {_distribution}"

        _LOGGER.debug(dbg_msg)

        _lights = hass.data[DOMAIN]["controller"].lights

        for _entity_id in _entity_ids:
            for casambi_light in _lights.values():
                if casambi_light.entity_id == _entity_id:
                    # entity found
                    params = {}
                    params["brightness"] = _brightness
                    if _distribution is not None:
                        params["distribution"] = _distribution

                    dbg_msg = "async_handle_platform_service_light_turn_on: "
                    dbg_msg += f"entity found: {_entity_id}, "
                    dbg_msg += f"setting params: {params}"
                    _LOGGER.debug(dbg_msg)

                    await casambi_light.async_turn_on(**params)

    # add platform service to turn on Casambi light
    hass.services.async_register(
        DOMAIN,
        SERVICE_CASAMBI_LIGHT_TURN_ON,
        async_handle_platform_service_light_turn_on,
    )

    return True
