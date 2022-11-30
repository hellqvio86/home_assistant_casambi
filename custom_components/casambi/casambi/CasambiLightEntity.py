"""
Support for Casambi lights.
"""
import logging

from typing import Any, Optional

from homeassistant.components.light import (
    LightEntity,
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP,
    ATTR_RGB_COLOR,
    ATTR_RGBW_COLOR,
    COLOR_MODE_BRIGHTNESS,
    COLOR_MODE_COLOR_TEMP,
    COLOR_MODE_RGB,
    COLOR_MODE_RGBW,
    SUPPORT_BRIGHTNESS,
)

try:
    from homeassistant.components.light import ATTR_DISTRIBUTION
except ImportError:
    ATTR_DISTRIBUTION = "distribution"

from homeassistant.helpers.update_coordinator import CoordinatorEntity

from ..const import (
    ATTR_SERV_BRIGHTNESS,
    ATTR_SERV_DISTRIBUTION,
)

from .CasambiEntity import CasambiEntity

_LOGGER = logging.getLogger(__name__)


class CasambiLightEntity(CoordinatorEntity, LightEntity, CasambiEntity):
    """Defines a Casambi Key Light."""

    def __init__(self, coordinator, unit, controller, hass):
        """Initialize Casambi Key Light."""
        CasambiEntity.__init__(self, unit, controller, hass)
        CoordinatorEntity.__init__(self, coordinator)

        self.idx = self.unique_id
        self._brightness: Optional[int] = None
        self._distribution: Optional[int] = None
        self._state: Optional[bool] = None
        self._temperature: Optional[int] = None

    @property
    def entity_registry_enabled_default(self) -> bool:
        """Whether or not the entity is enabled by default."""
        return True

    @property
    def available(self) -> bool:
        """
        Return True if entity is available.
        """
        _available = self.unit.online

        _LOGGER.debug(f"available is returning {_available} for unit={self.unit}")

        return _available

    @property
    def brightness(self) -> Optional[int]:
        """
        Return the brightness of this light between 1..255.
        """
        return self._brightness

    @property
    def distribution(self) -> Optional[int]:
        """
        Return the distribution of this light between 1..255.
        """
        return self._distribution

    @property
    def min_mireds(self) -> int:
        """
        Return the coldest color_temp that this light supports.

        M = 1000000 / T

        25000 K, has a mired value of M = 40 mireds
        1000000 / 25000 = 40
        """
        return self.unit.get_min_mired()

    @property
    def max_mireds(self) -> int:
        """
        Return the warmest color_temp that this light supports.

        M = 1000000 / T

        25000 K, has a mired value of M = 40 mireds
        1000000 / 25000 = 40

        {
            'Dimmer': {
                'type': 'Dimmer',
                'value': 0.0
                },
            'CCT': {
                'min': 2200,
                'max': 6000,
                'level': 0.4631578947368421,
                'type': 'CCT',
                'value': 3960.0
                }
        }
        """
        return self.unit.get_max_mired()

    @property
    def color_temp(self) -> int:
        """
        Return the CT color value in mireds.
        """
        return self.unit.get_color_temp()

    @property
    def rgb_color(self):
        """
        Getter for rgb color
        """
        return self.unit.get_rgb_color()

    @property
    def rgbw_color(self):
        """
        Getter for rgbe color
        """
        return self.unit.get_rgbw_color()

    @property
    def supported_features(self) -> int:
        """
        Flag supported features.

        This is deprecated and will be removed in Home Assistant 2021.10.
        """
        return SUPPORT_BRIGHTNESS

    @property
    def color_mode(self):
        """
        Set color mode for this entity.
        """
        if self.unit.supports_rgbw():
            return COLOR_MODE_RGBW
        if self.unit.supports_rgb():
            return COLOR_MODE_RGB
        if self.unit.supports_color_temperature():
            return COLOR_MODE_COLOR_TEMP
        if self.unit.supports_brightness():
            return COLOR_MODE_BRIGHTNESS

        return None

    @property
    def supported_color_modes(self):
        """
        Flag supported color_modes (in an array format).
        """
        supports = []

        if self.unit.supports_brightness():
            supports.append(COLOR_MODE_BRIGHTNESS)

        if self.unit.supports_color_temperature():
            supports.append(COLOR_MODE_COLOR_TEMP)

        if self.unit.supports_rgbw():
            supports.append(COLOR_MODE_RGBW)
        elif self.unit.supports_rgb():
            supports.append(COLOR_MODE_RGB)

        return supports

    @property
    def is_on(self) -> bool:
        """
        Return the state of the light.
        """
        return bool(self._state)

    @property
    def extra_state_attributes(self):
        """
        Getter for extra state attributes
        """
        return {
            "distribution": self._distribution,
        }

    def update_state(self):
        """
        Update units state
        """
        if self.enabled:
            # Device needs to be enabled for us to schedule updates
            _LOGGER.debug(f"update_state {self}")
            self.async_schedule_update_ha_state(True)

    def process_update(self, data):
        """Process callback message, update home assistant light state"""
        _LOGGER.debug(f"process_update: self: {self} data: {data}")

        if self.enabled:
            # Device needs to be enabled for us to schedule updates
            self.async_schedule_update_ha_state(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """
        Turn light off
        """
        _LOGGER.debug(f"async_turn_off {self}")

        await self.unit.turn_unit_off()

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the light."""
        _LOGGER.debug(f"async_turn_on {self} unit: {self.unit} kwargs: {kwargs}")
        brightness = 255
        distribution = 255

        if ATTR_COLOR_TEMP in kwargs:
            dbg_msg = "async_turn_on: ATTR_COLOR_TEMP:"
            dbg_msg += f" {kwargs[ATTR_COLOR_TEMP]}"
            _LOGGER.debug(dbg_msg)

            color_temp = kwargs[ATTR_COLOR_TEMP]

            dbg_msg = "async_turn_on:"
            dbg_msg += f"setting unit color name={self.name}"
            dbg_msg += f" color_temp={color_temp}"
            _LOGGER.debug(dbg_msg)

            await self.unit.set_unit_color_temperature(value=color_temp, source="mired")

            return

        if ATTR_RGBW_COLOR in kwargs:
            (red, green, blue, white) = kwargs[ATTR_RGBW_COLOR]

            dbg_msg = "async_turn_on:"
            dbg_msg += f"setting unit color name={self.name}"
            dbg_msg += f" rgbw=({red}, {green}, {blue}, {white})"
            _LOGGER.debug(dbg_msg)

            await self.unit.set_unit_rgbw(
                color_value=(red, green, blue, white),
            )

            return

        if ATTR_RGB_COLOR in kwargs:
            (red, green, blue) = kwargs[ATTR_RGB_COLOR]

            dbg_msg = "async_turn_on:"
            dbg_msg += f"setting unit color name={self.name}"
            dbg_msg += f" rgb=({red}, {green}, {blue})"
            _LOGGER.debug(dbg_msg)

            await self.unit.set_unit_rgb(
                color_value=(red, green, blue), send_rgb_format=True
            )

            return

        if ATTR_BRIGHTNESS in kwargs:
            brightness = round((kwargs[ATTR_BRIGHTNESS] / 255.0), 2)

        if brightness == 255:
            dbg_msg = "async_turn_on:"
            dbg_msg += f"turning unit on name={self.name}"
            _LOGGER.debug(dbg_msg)

            await self.unit.turn_unit_on()
        else:
            dbg_msg = "async_turn_on:"
            dbg_msg += f"setting units brightness name={self.name}"
            dbg_msg += f" brightness={brightness}"
            _LOGGER.debug(dbg_msg)

            await self.unit.set_unit_value(value=brightness)

        if ATTR_DISTRIBUTION in kwargs:
            distribution = round((kwargs[ATTR_DISTRIBUTION] / 255.0), 2)

            dbg_msg = "async_turn_on:"
            dbg_msg += f"setting units distribution name={self.name}"
            dbg_msg += f" distribution={distribution}"
            _LOGGER.debug(dbg_msg)

            await self.unit.set_unit_distribution(distribution=distribution)

    async def async_update(self) -> None:
        """Update Casambi entity."""
        if self.unit.online:
            if self.unit.value > 0:
                self._state = True
                self._brightness = int(round(self.unit.value * 255))
                self._distribution = int(round(self.unit.distribution * 255))
            else:
                self._state = False
        _LOGGER.debug(f"async_update {self}")

    async def async_handle_entity_service_light_turn_on(self, **kwargs: Any) -> None:
        """Handle turn on of Casambi light when setup from UI integration."""
        # Get parameters
        _brightness = kwargs.get(ATTR_SERV_BRIGHTNESS)
        _distribution = kwargs.get(ATTR_SERV_DISTRIBUTION, None)

        dbg_msg = f"async_handle_entity_service_light_turn_on: self: {self}, "
        dbg_msg += f"kwargs: {kwargs}, brightness: {_brightness}, "
        dbg_msg += f"distribution: {_distribution}"
        _LOGGER.debug(dbg_msg)

        params = {}
        params["brightness"] = _brightness
        if _distribution is not None:
            params["distribution"] = _distribution

        dbg_msg = "async_handle_entity_service_light_turn_on: entity: "
        dbg_msg += f"{self.entity_id}, setting params: {params}"
        _LOGGER.debug(dbg_msg)

        await self.async_turn_on(**params)

    def __repr__(self) -> str:
        """Return the representation."""
        name = self.unit.name

        result = f"<Casambi light {name}: unit={self.unit}>"

        return result
