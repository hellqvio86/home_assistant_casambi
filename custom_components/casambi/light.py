"""
Support for Casambi lights.
For more details about this component, please refer to the documentation at
https://home-assistant.io/components/@todo
"""

import logging
import voluptuous as vol

from homeassistant.components.light import ATTR_BRIGHTNESS

try:
    from homeassistant.components.light import ATTR_DISTRIBUTION
except ImportError:
    ATTR_DISTRIBUTION = "distribution"

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.helpers import entity_platform

from .const import (
    DOMAIN,
    CONF_CONTROLLER,
    CONF_COORDINATOR,
    SERVICE_CASAMBI_LIGHT_TURN_ON,
    ATTR_SERV_BRIGHTNESS,
    ATTR_SERV_DISTRIBUTION,
    ATTR_SERV_ENTITY_ID,
)

from .casambi.CasambiLightEntity import CasambiLightEntity
from .utils import async_create_controller, async_create_coordinator

_LOGGER = logging.getLogger(__name__)

CASAMBI_CONTROLLER = None


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities,
):
    """
    Setup sensors from a config entry created in the integrations UI.
    """
    controller = hass.data[DOMAIN][CONF_CONTROLLER]
    coordinator = hass.data[DOMAIN][CONF_COORDINATOR]

    _LOGGER.debug(
        f"Arguments for light sensor entities: hass: {hass}, config_entry: {config_entry} controller: {controller} async_add_entities: {async_add_entities}"
    )

    units = controller.aiocasambi_controller.get_units()
    for unit in units:
        if not unit.is_light():
            continue

        casambi_light = CasambiLightEntity(coordinator, unit, controller, hass)
        async_add_entities([casambi_light], True)

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
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities,
    discovery_info=None,
):
    """
    Setup Casambi platform, called when setup through configuration.yaml
    """
    warn_msg = "Using Casambi integration through configuration.yaml is "
    warn_msg += "deprecated, please consider to "
    warn_msg += "switch to configuration flow!"
    _LOGGER.warning(warn_msg)

    if CONF_CONTROLLER in hass.data[DOMAIN]:
        dbg_msg = "async_setup_platform CasambiController already created!"
        _LOGGER.debug(dbg_msg)
        return

    config = hass.data[DOMAIN][config_entry.entry_id]
    controller = hass.data[DOMAIN][CONF_CONTROLLER] = await async_create_controller(
        hass, config
    )
    if not controller:
        return False
    coordinator = hass.data[DOMAIN][CONF_COORDINATOR] = await async_create_coordinator(
        hass, config, controller
    )

    units = controller.aiocasambi_controller.get_units()
    for unit in units:
        if not unit.is_light():
            continue

        casambi_light = CasambiLightEntity(
            coordinator, unit, controller.aiocasambi_controller, hass
        )
        async_add_entities([casambi_light], True)

        controller.lights[casambi_light.unique_id] = casambi_light

    @callback
    async def async_handle_platform_service_light_turn_on(call: ServiceCall) -> None:
        """Handle turn on of Casambi light when setup from yaml."""
        dbg_msg = f"ServiceCall {call.domain}.{call.service}, "
        dbg_msg += "data: {call.data}"
        _LOGGER.debug(dbg_msg)

        # Check if entities were selected
        if ATTR_SERV_ENTITY_ID not in call.data:
            # service handle currently only supports selection of entities
            err_msg = f"ServiceCall {call.domain}.{call.service}:"
            err_msg += " No entity was specified."
            err_msg += " Please specify entities instead of areas or devices."
            _LOGGER.error(err_msg)

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
