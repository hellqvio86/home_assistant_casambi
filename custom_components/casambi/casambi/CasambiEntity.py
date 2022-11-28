"""
Support for Casambi lights.
"""
import logging

from typing import Any, Dict

from homeassistant.const import ATTR_NAME
from homeassistant.helpers.entity import DeviceInfo, Entity

from ..const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class CasambiEntity(Entity):
    """Defines a Casambi Entity."""
    _attr_has_entity_name = True

    def __init__(self, unit, controller, hass, name: str = None):
        """Initialize Casambi Entity."""
        _LOGGER.debug(f"Casambi entity - init - start")
        self.unit = unit
        self.controller = controller
        self.hass = hass
        self._unit_unique_id = unit.unique_id
        self._attr_name = name

        controller.entities.append(self)

        _LOGGER.debug(f"Casambi entity - init - end")

    @property
    def unique_id(self) -> str:
        """Return the unique ID for this sensor."""
        name = self.unit.unique_id
        if self._attr_name:
            name += f"_{self._attr_name}"
        return name.lower()

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information about this Casambi Key Light."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.unit.unique_id)},
            name=self.unit.name,
            default_manufacturer="Casambi",
            manufacturer=self.unit.oem,
            default_model="Casambi",
            model=self.unit.fixture_model,
            sw_version=self.unit.firmware_version,
        )

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.unit.online

    @property
    def should_poll(self):
        """Disable polling by returning False"""
        return False

    def __repr__(self) -> str:
        """Return the representation."""
        return f"<Casambi {self.unit.name}: unit={self.unit}>"
