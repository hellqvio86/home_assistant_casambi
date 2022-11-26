import logging

from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.helpers.entity import EntityCategory

from .CasambiBinarySensorEntity import CasambiBinarySensorEntity

_LOGGER = logging.getLogger(__name__)


class CasambiStatusBinarySensorEntity(CasambiBinarySensorEntity):
    def __init__(self, unit, controller, hass):
        _LOGGER.debug(f"Casambi status binary sensor - init - start")

        CasambiBinarySensorEntity.__init__(self, unit, controller, hass,
            "Status", BinarySensorDeviceClass.CONNECTIVITY)

        # self._attr_is_on = False
        self._attr_state = self.unit.online

        _LOGGER.debug(f"Casambi status binary sensor - init - end")

    @property
    def entity_category(self):
        return EntityCategory.DIAGNOSTIC

    # @property
    # def state(self):
    #     return self.controller.units[self._unit_unique_id].online

    async def async_update(self) -> None:
        """Update Casambi entity."""
        self._attr_state = self.unit.online
        _LOGGER.debug(f"async_update {self}")

    def process_update(self, data):
        """Process callback message, update home assistant light state"""
        _LOGGER.debug(f"process_update: self: {self} data: {data}")
        if self.enabled:
            # Device needs to be enabled for us to schedule updates
            self.async_schedule_update_ha_state(True)

    def __repr__(self) -> str:
        """Return the representation."""
        return f"<Casambi status binary sensor {self.unit.name}: unit={self.unit}"
