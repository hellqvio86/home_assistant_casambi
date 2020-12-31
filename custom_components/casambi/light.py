"""
Support for Casambi lights.
For more details about this component, please refer to the documentation at
https://home-assistant.io/components/@todo
"""
import logging
import ssl
import asyncio
import aiocasambi
import async_timeout

from datetime import timedelta
from typing import Any, Callable, Dict, List, Optional

import voluptuous as vol

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    SUPPORT_BRIGHTNESS,
    LightEntity,
)
from homeassistant.core import HomeAssistant
from homeassistant.core import callback
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_NAME
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.typing import HomeAssistantType
from homeassistant.helpers import aiohttp_client
from homeassistant.const import CONF_EMAIL, CONF_API_KEY

from aiocasambi.websocket import STATE_DISCONNECTED, STATE_STOPPED, STATE_RUNNING

import homeassistant.helpers.config_validation as cv

from .const import (
    DOMAIN,
    WIRE_ID,
    CONF_USER_PASSWORD,
    CONF_NETWORK_PASSWORD,
    ATTR_IDENTIFIERS,
    ATTR_MANUFACTURER,
    ATTR_MODEL,
    ATTR_SOFTWARE_VERSION,
    SCAN_INTERVAL_TIME_SECS
)

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_USER_PASSWORD): cv.string,
        vol.Required(CONF_NETWORK_PASSWORD): cv.string,
        vol.Required(CONF_EMAIL): cv.string,
        vol.Required(CONF_API_KEY): cv.string,
    })
}, extra=vol.ALLOW_EXTRA)

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=SCAN_INTERVAL_TIME_SECS)


async def async_setup_platform(hass: HomeAssistant, config: dict, async_add_entities, discovery_info=None):

    user_password = config[CONF_USER_PASSWORD]
    network_password = config[CONF_NETWORK_PASSWORD]
    email = config[CONF_EMAIL]
    api_key = config[CONF_API_KEY]

    sslcontext = ssl.create_default_context()
    session = aiohttp_client.async_get_clientsession(hass)

    casambi_controller = CasambiController(hass)

    controller = aiocasambi.Controller(
        email=email,
        user_password=user_password,
        network_password=network_password,
        api_key=api_key,
        websession=session,
        sslcontext=sslcontext,
        wire_id=WIRE_ID,
        callback=casambi_controller.signalling_callback,
    )

    casambi_controller.controller = casambi_controller

    try:
        with async_timeout.timeout(10):
            await controller.create_user_session()
            await controller.create_network_session()
            await controller.start_websocket()

    except aiocasambi.LoginRequired:
        _LOGGER.error("Connected to casambi but couldn't log in")
        return False

    except aiocasambi.Unauthorized:
        _LOGGER.error("Connected to casambi but not registered")
        return False

    except (asyncio.TimeoutError, aiocasambi.RequestError):
        _LOGGER.error('Error connecting to the Casambi')
        return False

    except aiocasambi.AiocasambiException:
        _LOGGER.error('Unknown Casambi communication error occurred')
        return False

    await controller.initialize()

    units = controller.get_units()

    for unit in units:
        casambi_light = CasambiLight(unit, controller, hass)
        async_add_entities([casambi_light], True)

        casambi_controller.units[casambi_light.unique_id] = casambi_light

    return True


class CasambiController:
    """Manages a single UniFi Controller."""

    def __init__(self, hass, network_retry_timer=30, units = {}):
        """Initialize the system."""
        self._hass = hass
        self._controller = None
        self._network_retry_timer = network_retry_timer
        self.units = units

    @property
    def controller(self):
        return self._controller

    @controller.setter
    def controller(self, controller):
        self._controller = controller

    async def async_reconnect(self):
        _LOGGER.debug("async_reconnect: trying to connect to casambi")
        await self._controller.reconnect()

        if self._controller.get_websocket_state() != STATE_RUNNING:
            _LOGGER.debug(f"async_reconnect: could not connect to casambi, trying again in {self._network_retry_timer} seconds")

            # Try again to reconnect
            self._hass.loop.call_later(self._network_retry_timer, \
                self.async_reconnect)

    def set_all_units_offline(self):
        for key in self.units:
            self.units[key].set_online(False)

    def signalling_callback(self, signal, data):
        _LOGGER.debug(f"signalling_callback signal: {signal} data: {data}")
        if signal == aiocasambi.websocket.SIGNAL_DATA:
            for key, value in data.items():
                self.units[key].process_update(value)
        elif signal == aiocasambi.websocket.SIGNAL_CONNECTION_STATE and \
            (data == aiocasambi.websocket.STATE_STOPPED):
            _LOGGER.debug("signalling_callback websocket STATE_STOPPED")

            hass = None

            # Set all units to offline
            self.set_all_units_offline()

            _LOGGER.debug("signalling_callback: creating reconnection")
            hass.loop.create_task(self.async_reconnect())
        elif signal == signal == aiocasambi.websocket.SIGNAL_CONNECTION_STATE and \
            (data == aiocasambi.websocket.STATE_DISCONNECTED):
            _LOGGER.debug("signalling_callback websocket STATE_DISCONNECTED")

            hass = None

            # Set all units to offline
            self.set_all_units_offline()

            _LOGGER.debug("signalling_callback: creating reconnection")
            hass.loop.create_task(self.async_reconnect())


class CasambiLight(LightEntity):
    """Defines a Casambi Key Light."""

    def __init__(
        self, unit, controller, hass
    ):
        """Initialize Casambi Key Light."""
        self._brightness: Optional[int] = None
        self._state: Optional[bool] = None
        self._temperature: Optional[int] = None
        self.unit = unit
        self.controller = controller
        self.hass = hass

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        return self.unit.name

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.unit.online

    @property
    def unique_id(self) -> str:
        """Return the unique ID for this sensor."""
        return self.unit.unique_id

    @property
    def brightness(self) -> Optional[int]:
        """Return the brightness of this light between 1..255."""
        return self._brightness

    @property
    def supported_features(self) -> int:
        """Flag supported features."""
        return SUPPORT_BRIGHTNESS

    @property
    def is_on(self) -> bool:
        """Return the state of the light."""
        return bool(self._state)
    
    def set_online(self, online):
        self.unit.online = online

        _LOGGER.debug(f"set_online to {online} for unit {self}")

        self.async_schedule_update_ha_state(True)

    def process_update(self, data):
        """Process callback message, update home assistant light state"""
        _LOGGER.debug(f"process_update self: {self} data: {data}")

        #if data.value > 0:
        #    self._state = True
        #    self._brightness = int(math.ceil(data.value * 255))
        #else:
        #    self._state = False
        self.async_schedule_update_ha_state(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        _LOGGER.debug(f"async_turn_off {self}")

        await self.unit.turn_unit_off()

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the light."""
        _LOGGER.debug(f"async_turn_on {self} kwargs: {kwargs}")
        brightness = 255

        if ATTR_BRIGHTNESS in kwargs:
            brightness = round((kwargs[ATTR_BRIGHTNESS] / 255.0),2)

        if brightness == 255:
            await self.unit.turn_unit_on()
        else:
            await self.unit.set_unit_value(value=brightness)

    @property
    def should_poll(self):
        """Disable polling by returning False"""
        return False

    async def async_update(self) -> None:
        """Update Casambi entity."""
        if self.unit.value > 0:
            self._state = True
            self._brightness = int(round(self.unit.value * 255))
        else:
            self._state = False
        _LOGGER.debug(f"async_update {self}")

        if not self.unit.online:
            _LOGGER.error(f"unit is not online: {self}")

    @property
    def device_info(self) -> Dict[str, Any]:
        """Return device information about this Casambi Key Light."""
        #return {
        #    ATTR_IDENTIFIERS: {(DOMAIN, self._info.serial_number)},
        #    ATTR_NAME: self._info.product_name,
        #    ATTR_MANUFACTURER: "Casambi",
        #    ATTR_MODEL: self._info.product_name,
        #    ATTR_SOFTWARE_VERSION: f"{self._info.firmware_version} ({self._info.firmware_build_number})",
        #}
        model = 'Casambi'
        manufacturer = 'Casambi'

        if self.unit.fixture_model:
            model = self.unit.fixture_model

        if self.unit.oem:
            manufacturer =  self.unit.oem

        return {
            ATTR_IDENTIFIERS: {(DOMAIN, self.unique_id)},
            ATTR_NAME: self.unit.name,
            ATTR_MANUFACTURER: manufacturer,
            ATTR_MODEL: model,
        }

    def __repr__(self) -> str:
        """Return the representation."""
        name = self.unit.name

        result = f"<Casambi light {name}: unit={self.unit}"

        return result
