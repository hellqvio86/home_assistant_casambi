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
    coordinator = hass.data[DOMAIN]["coordinator"]
    await coordinator.async_refresh()

    units = casambi_controller.controller.get_units()
    binarySensors = []

    for unit in units:
        _LOGGER.debug("Adding CasambiStatusBinarySensorEntity...")
        binarySensors.append(CasambiStatusBinarySensorEntity(unit, casambi_controller.controller, hass))

        # TODO: check for overheat control
        # 'controls': [[{'name': 'overheat', 'type': 'Overheat', 'status': 'ok'}, {'name': 'dimmer0', 'type': 'Dimmer', 'value': 0.0}]]
        # if ...
          #  _LOGGER.debug("Adding CasambiOverheatBinarySensorEntity...")
          #  binarySensors.append(CasambiOverheatBinarySensorEntity(unit, casambi_controller.controller, hass))

    if binarySensors:
        _LOGGER.debug("Adding binary sensor entities...")
        async_add_entities(binarySensors)
    else:
        _LOGGER.debug("No binary sensor entities available.")

    return True
