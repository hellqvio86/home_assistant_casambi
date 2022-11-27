import logging

from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.const import STATE_OFF, STATE_ON
from homeassistant.helpers.entity import EntityCategory

from .CasambiBinarySensorEntity import CasambiBinarySensorEntity

_LOGGER = logging.getLogger(__name__)


class CasambiStatusBinarySensorEntity(CasambiBinarySensorEntity):
    def __init__(self, unit, controller, hass):
        _LOGGER.debug(f"Casambi status binary sensor - init - start")

        CasambiBinarySensorEntity.__init__(self, unit, controller, hass,
            "Status", BinarySensorDeviceClass.CONNECTIVITY)

        _LOGGER.debug(f"Casambi status binary sensor - init - end")

    @property
    def entity_category(self):
        return EntityCategory.DIAGNOSTIC

    @property
    def available(self) -> bool:
        """Connectivity entity is always availble."""
        return True

    @property
    def state(self):
        return STATE_ON if self.unit.online else STATE_OFF

    def update_state(self):
        """Update units state"""
        if self.enabled:
            # Device needs to be enabled for us to schedule updates
            _LOGGER.debug(f"update_state {self}")
            self.async_schedule_update_ha_state(True)

    def process_update(self, data):
        """Process callback message, update home assistant light state"""
        _LOGGER.debug(f"process_update: self: {self} data: {data}")
        if self.enabled:
            if self._unit_unique_id in data:
                # Device needs to be enabled for us to schedule updates
                self.async_schedule_update_ha_state(True)

    def __repr__(self) -> str:
        """Return the representation."""
        return f"<Casambi status binary sensor {self.unit.name}: unit={self.unit}>"
