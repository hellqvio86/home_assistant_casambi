import logging

from homeassistant.components.binary_sensor import BinarySensorDeviceClass

from .CasambiBinarySensorEntity import CasambiBinarySensorEntity

_LOGGER = logging.getLogger(__name__)

NAME = "Overheat"

class CasambiOverheatBinarySensorEntity(CasambiBinarySensorEntity):
    def __init__(self, unit, controller, hass):
        _LOGGER.debug(f"Casambi {NAME} binary sensor - init - start")

        CasambiBinarySensorEntity.__init__(self, unit, controller, hass,
            NAME, BinarySensorDeviceClass.HEAT)

        _LOGGER.debug(f"Casambi {NAME} binary sensor - init - end")

    def __repr__(self) -> str:
        """Return the representation."""
        return f"<Casambi {NAME} binary sensor {self.unit.name}: unit={self.unit}"
