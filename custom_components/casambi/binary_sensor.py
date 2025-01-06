"""
Binary Sensor implementation for Casambi
"""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .casambi.CasambiStatusBinarySensorEntity import CasambiStatusBinarySensorEntity
from .const import (
    DOMAIN,
    CONF_CONTROLLER,
)

_LOGGER = logging.getLogger(__name__)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """
    Support unloading of entry
    """
    return True


async def async_setup_entry(
    hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities
):
    """
    Setting up binary sensor
    """
    _LOGGER.debug(f"Setting up binary sensor entities. config_entry:{config_entry}")

    controller = hass.data[DOMAIN][CONF_CONTROLLER]

    units = controller.aiocasambi_controller.get_units()
    binary_sensors = []

    for unit in units:
        _LOGGER.debug("Adding CasambiStatusBinarySensorEntity...")
        binary_sensors.append(CasambiStatusBinarySensorEntity(unit, controller, hass))

        # TODO: check for overheat control
        # 'controls': [[{'name': 'overheat', 'type': 'Overheat', 'status': 'ok'}, ...]]
        # if ...
        #   _LOGGER.debug("Adding CasambiOverheatBinarySensorEntity...")
        #   binary_sensors.append(CasambiOverheatBinarySensorEntity(unit, controller, hass))

    if binary_sensors:
        _LOGGER.debug("Adding binary sensor entities...")
        async_add_entities(binary_sensors)
    else:
        _LOGGER.debug("No binary sensor entities available.")

    return True
