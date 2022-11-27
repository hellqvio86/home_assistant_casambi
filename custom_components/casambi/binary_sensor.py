import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .casambi.CasambiOverheatBinarySensorEntity import CasambiOverheatBinarySensorEntity
from .casambi.CasambiStatusBinarySensorEntity import CasambiStatusBinarySensorEntity
from .const import (
    DOMAIN,
    CONF_CONTROLLER,
)

_LOGGER = logging.getLogger(__name__)

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    return True

async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities):
    _LOGGER.debug("Setting up binary sensor entities.")
    # config = hass.data[DOMAIN][config_entry.entry_id]

    # TODO: extract casambi controller from light entity
    casambi_controller = hass.data[DOMAIN][CONF_CONTROLLER]

    units = casambi_controller.aiocasambi_controller.get_units()
    binary_sensors = []

    for unit in units:
        _LOGGER.debug("Adding CasambiStatusBinarySensorEntity...")
        binary_sensors.append(CasambiStatusBinarySensorEntity(unit, casambi_controller, hass))
        
        # TODO: check for overheat control
        # 'controls': [[{'name': 'overheat', 'type': 'Overheat', 'status': 'ok'}, {'name': 'dimmer0', 'type': 'Dimmer', 'value': 0.0}]]
        # if ...
          #  _LOGGER.debug("Adding CasambiOverheatBinarySensorEntity...")
          #  binary_sensors.append(CasambiOverheatBinarySensorEntity(unit, casambi_controller, hass))

    if binary_sensors:
        _LOGGER.debug("Adding binary sensor entities...")
        async_add_entities(binary_sensors)
    else:
        _LOGGER.debug("No binary sensor entities available.")

    return True
