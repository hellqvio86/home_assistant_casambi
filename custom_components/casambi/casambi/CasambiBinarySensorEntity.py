import logging

from homeassistant.core import HomeAssistant
from homeassistant.components.binary_sensor import BinarySensorEntity

from ..const import DOMAIN
from .CasambiEntity import CasambiEntity

_LOGGER = logging.getLogger(__name__)

class CasambiBinarySensorEntity(BinarySensorEntity, CasambiEntity):
    def __init__(self, unit, controller, hass, name_suffix: str = "", icon=None, device_class=None):
        _LOGGER.debug(f"Casambi {name_suffix} - init - start")

        self._attr_is_on = False
        self._hass = hass
        self._attr_icon = icon
        self._attr_device_class = device_class

        CasambiEntity.__init__(self, unit, controller, hass)
        BinarySensorEntity.__init__(self)

        _LOGGER.debug(f"Casambi {name_suffix} - init - end")

    @property
    def state(self):
        return self._attr_state
