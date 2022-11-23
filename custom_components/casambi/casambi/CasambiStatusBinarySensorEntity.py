import logging

from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.helpers.entity import EntityCategory

from .CasambiBinarySensorEntity import CasambiBinarySensorEntity

_LOGGER = logging.getLogger(__name__)

_ENTITY_SUFFIX = "Status"

class CasambiStatusBinarySensorEntity(CasambiBinarySensorEntity):
    def __init__(self, unit, controller, hass):
        _LOGGER.debug(f"Casambi {name_suffix} binary sensor - init - start")

        self._hass = hass
        self._attr_icon = icon
        self._attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
        self._attr_is_on = False
        CasambiBinarySensorEntity.__init__(self, unit, controller, hass, _ENTITY_SUFFIX)

        _LOGGER.debug(f"Casambi {name_suffix} binary sensor - init - end")

    @property
    def entity_category(self):
        return EntityCategory.DIAGNOSTICS

    def __repr__(self) -> str:
        """Return the representation."""
        return f"<Casambi {_ENTITY_SUFFIX} binary sensor {self.unit.name}: unit={self.unit}"
