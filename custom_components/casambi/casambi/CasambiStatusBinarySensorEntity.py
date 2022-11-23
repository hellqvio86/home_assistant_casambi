
import logging

from .CasambiBinarySensorEntity import CasambiBinarySensorEntity


_LOGGER = logging.getLogger(__name__)

_ENTITY_SUFFIX = "Status"

class CasambiStatusBinarySensorEntity(CasambiBinarySensorEntity):
    def __init__(self, unit, controller, hass):
        CasambiBinarySensorEntity.__init__(
            self, unit, controller, hass,
            _ENTITY_SUFFIX,
            # "mdi:google-lens",
        )

        # self._attr_icon = "mdi:light-flood-down"

    def update_state(self):
        """
        Update units state
        """
        if self.enabled:
            # Device needs to be enabled for us to schedule updates
            _LOGGER.debug(f"update_state {self}")
            self.async_schedule_update_ha_state(True)

    # def process_update(self, data):
    #     """Process callback message, update home assistant light state"""
    #     _LOGGER.debug(f"process_update: self: {self} data: {data}")

    #     if self.enabled:
    #         # Device needs to be enabled for us to schedule updates
    #         self.async_schedule_update_ha_state(True)

    async def async_update(self) -> None:
        """Update Casambi entity."""
        _LOGGER.info(f"async_update: unit is not online: {self}")

        if not self.unit.online:
          self._attr_state = True
        else:
          self._attr_state = False

        # else:
            # if self.unit.value > 0:
                # self._state = True
                # self._brightness = int(round(self.unit.value * 255))
                # self._distribution = int(round(self.unit.distribution * 255))
            # else:
            #     self._state = False
        _LOGGER.debug(f"async_update {self}")

    def __repr__(self) -> str:
        """Return the representation."""
        name = self.unit.name

        result = f"<Casambi {_ENTITY_SUFFIX} binary sensor {name}: unit={self.unit}"

        return result
