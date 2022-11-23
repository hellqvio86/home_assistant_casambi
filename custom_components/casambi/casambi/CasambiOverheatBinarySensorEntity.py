import logging

from homeassistant.components.binary_sensor import BinarySensorDeviceClass

from .CasambiBinarySensorEntity import CasambiBinarySensorEntity

_LOGGER = logging.getLogger(__name__)

_ENTITY_SUFFIX = "Overheat"

class CasambiOverheatBinarySensorEntity(CasambiBinarySensorEntity):
    def __init__(self, unit, controller, hass):
        _LOGGER.debug(f"Casambi {_ENTITY_SUFFIX} binary sensor - init - start")

        self._hass = hass
        #self._attr_icon = icon
        self._attr_device_class = BinarySensorDeviceClass.HEAT
        self._attr_is_on = False
        CasambiBinarySensorEntity.__init__(self, unit, controller, hass, _ENTITY_SUFFIX)

        _LOGGER.debug(f"Casambi {_ENTITY_SUFFIX} binary sensor - init - end")

    def __repr__(self) -> str:
        """Return the representation."""
        return f"<Casambi {_ENTITY_SUFFIX} binary sensor {self.unit.name}: unit={self.unit}"
