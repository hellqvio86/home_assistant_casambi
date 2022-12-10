import logging

from homeassistant.components.binary_sensor import BinarySensorDeviceClass

from .CasambiBinarySensorEntity import CasambiBinarySensorEntity

_LOGGER = logging.getLogger(__name__)


class CasambiOverheatBinarySensorEntity(CasambiBinarySensorEntity):
    def __init__(self, unit, controller, hass):
        _LOGGER.debug("Casambi overheat binary sensor - init - start")

        CasambiBinarySensorEntity.__init__(
            self, unit, controller, hass, "Overheat", BinarySensorDeviceClass.HEAT
        )

        _LOGGER.debug("Casambi overheat binary sensor - init - end")

    def __repr__(self) -> str:
        """Return the representation."""
        return f"<Casambi overheat binary sensor {self.unit.name}: unit={self.unit}>"
