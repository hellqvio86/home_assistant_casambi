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

    def __init__(self, unit, controller, hass):
        """Initialize Casambi Entity."""
        self.unit = unit
        self.controller = controller
        self.hass = hass

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        return self.unit.name

    @property
    def unique_id(self) -> str:
        """Return the unique ID for this sensor."""
        return self.unit.unique_id

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information about this Casambi Key Light."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.unit.unique_id)},
            name=self.unit.name,
            default_manufacturer = "Casambi",
            manufacturer = self.unit.oem,
            default_model = "Casambi",
            model = self.unit.fixture_model,
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
