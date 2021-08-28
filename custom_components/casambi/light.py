"""
Support for Casambi lights.
For more details about this component, please refer to the documentation at
https://home-assistant.io/components/@todo
"""
import logging
import ssl
import asyncio

import async_timeout
import aiocasambi
from aiocasambi.consts import (
    SIGNAL_DATA,
    STATE_RUNNING,
    SIGNAL_CONNECTION_STATE,
    STATE_DISCONNECTED,
    STATE_STOPPED,
    SIGNAL_UNIT_PULL_UPDATE
)

from typing import Any, Dict, Optional
from datetime import timedelta

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    SUPPORT_BRIGHTNESS,
    LightEntity,
    ATTR_COLOR_TEMP,
    ATTR_RGB_COLOR,
    ATTR_RGBW_COLOR,
    COLOR_MODE_BRIGHTNESS,
    COLOR_MODE_COLOR_TEMP,
    COLOR_MODE_RGB,
    COLOR_MODE_RGBW
)

from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from homeassistant import config_entries, core
from homeassistant.core import HomeAssistant
from homeassistant.const import ATTR_NAME
from homeassistant.helpers import aiohttp_client
from homeassistant.const import (
    CONF_EMAIL,
    CONF_API_KEY,
    CONF_SCAN_INTERVAL
)

from .const import (
    DOMAIN,
    WIRE_ID,
    CONFIG_SCHEMA,
    CONF_CONTROLLER,
    CONF_USER_PASSWORD,
    CONF_NETWORK_PASSWORD,
    CONF_NETWORK_TIMEOUT,
    ATTR_IDENTIFIERS,
    ATTR_MANUFACTURER,
    ATTR_MODEL,
    DEFAULT_NETWORK_TIMEOUT,
    DEFAULT_POLLING_TIME
)

_LOGGER = logging.getLogger(__name__)

CASAMBI_CONTROLLER = None


async def async_setup_entry(
        hass: core.HomeAssistant,
        config_entry: config_entries.ConfigEntry,
        async_add_entities,
):
    """Setup sensors from a config entry created in the integrations UI."""
    config = hass.data[DOMAIN][config_entry.entry_id]
    user_password = config[CONF_USER_PASSWORD]
    network_password = config[CONF_NETWORK_PASSWORD]
    email = config[CONF_EMAIL]
    api_key = config[CONF_API_KEY]

    network_timeout = DEFAULT_NETWORK_TIMEOUT
    scan_interval = DEFAULT_POLLING_TIME

    if CONF_NETWORK_TIMEOUT in config:
        network_timeout = config[CONF_NETWORK_TIMEOUT]

    if CONF_SCAN_INTERVAL in config:
        scan_interval = config[CONF_SCAN_INTERVAL]

    sslcontext = ssl.create_default_context()
    session = aiohttp_client.async_get_clientsession(hass)

    if CONF_CONTROLLER in hass.data[DOMAIN]:
        dbg_msg = 'async_setup_platform CasambiController already created!'
        _LOGGER.debug(dbg_msg)
        return

    hass.data[DOMAIN][CONF_CONTROLLER] = CasambiController(hass)
    casambi_controller = hass.data[DOMAIN][CONF_CONTROLLER]

    controller = aiocasambi.Controller(
        email=email,
        user_password=user_password,
        network_password=network_password,
        api_key=api_key,
        websession=session,
        sslcontext=sslcontext,
        wire_id=WIRE_ID,
        callback=casambi_controller.signalling_callback,
        network_timeout=network_timeout,
    )

    casambi_controller.controller = controller

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

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        # Name of the data. For logging purposes.
        name="light",
        update_method=casambi_controller.async_update_data,
        # Polling interval. Will only be polled if there are subscribers.
        update_interval=timedelta(seconds=scan_interval),
    )

    await coordinator.async_refresh()

    for unit in units:
        casambi_light = CasambiLight(coordinator,
                                     unit.unique_id,
                                     unit,
                                     controller,
                                     hass)
        async_add_entities([casambi_light], True)

        casambi_controller.units[casambi_light.unique_id] = casambi_light

    return True


async def async_setup_platform(
        hass: HomeAssistant,
        config: dict,
        async_add_entities,
        discovery_info=None
    ):
    '''
    Setup Casambi platform
    '''
    user_password = config[CONF_USER_PASSWORD]
    network_password = config[CONF_NETWORK_PASSWORD]
    email = config[CONF_EMAIL]
    api_key = config[CONF_API_KEY]

    network_timeout = DEFAULT_NETWORK_TIMEOUT
    scan_interval = DEFAULT_POLLING_TIME

    if CONF_NETWORK_TIMEOUT in config:
        network_timeout = config[CONF_NETWORK_TIMEOUT]

    if CONF_SCAN_INTERVAL in config:
        scan_interval = config[CONF_SCAN_INTERVAL]

    sslcontext = ssl.create_default_context()
    session = aiohttp_client.async_get_clientsession(hass)

    if CONF_CONTROLLER in hass.data[DOMAIN]:
        dbg_msg = 'async_setup_platform CasambiController already created!'
        _LOGGER.debug(dbg_msg)
        return

    hass.data[DOMAIN][CONF_CONTROLLER] = CasambiController(hass)
    casambi_controller = hass.data[DOMAIN][CONF_CONTROLLER]

    controller = aiocasambi.Controller(
        email=email,
        user_password=user_password,
        network_password=network_password,
        api_key=api_key,
        websession=session,
        sslcontext=sslcontext,
        wire_id=WIRE_ID,
        callback=casambi_controller.signalling_callback,
        network_timeout=network_timeout,
    )

    casambi_controller.controller = controller

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

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        # Name of the data. For logging purposes.
        name="light",
        update_method=casambi_controller.async_update_data,
        # Polling interval. Will only be polled if there are subscribers.
        update_interval=timedelta(seconds=scan_interval),
    )

    await coordinator.async_refresh()

    for unit in units:
        casambi_light = CasambiLight(coordinator,
                                     unit.unique_id,
                                     unit,
                                     controller,
                                     hass)
        async_add_entities([casambi_light], True)

        casambi_controller.units[casambi_light.unique_id] = casambi_light

    return True


class CasambiController:
    """Manages a single UniFi Controller."""

    def __init__(self, hass, network_retry_timer=30, units={}):
        """Initialize the system."""
        self._hass = hass
        self._controller = None
        self._network_retry_timer = network_retry_timer
        self.units = units

    @property
    def controller(self):
        '''
        Getter for controller
        '''
        return self._controller

    @controller.setter
    def controller(self, controller):
        '''
        Setter for controller
        '''
        self._controller = controller

    async def async_update_data(self):
        ''' Function for polling network state (state of lights) '''
        _LOGGER.debug('async_update_data started')
        try:
            await self._controller.get_network_state()
        except aiocasambi.LoginRequired:
            # Need to reconnect, session is invalid
            await self.async_reconnect()

    async def async_reconnect(self):
        '''
        Reconnect to the Internet API
        '''
        _LOGGER.debug("async_reconnect: trying to connect to casambi")
        await self._controller.reconnect()

        if self._controller.get_websocket_state() != STATE_RUNNING:
            msg = 'async_reconnect: could not connect to casambi. '
            msg += f"trying again in {self._network_retry_timer} seconds"
            _LOGGER.debug(msg)

            # Try again to reconnect
            self._hass.loop.call_later(self._network_retry_timer,
                                       self.async_reconnect)

    def update_unit_state(self, unit):
        '''
        Update unit state
        '''
        _LOGGER.debug(f"update_unit_state: unit: {unit} units: {self.units}")
        if unit in self.units:
            self.units[unit].update_state()

    def update_all_units(self):
        '''
        Update all the units state
        '''
        for key in self.units:
            self.units[key].update_state()

    def set_all_units_offline(self):
        '''
        Set all units to offline
        '''
        for key in self.units:
            self.units[key].set_online(False)

    def signalling_callback(self, signal, data):
        '''
        Signalling callback
        '''

        _LOGGER.debug(f"signalling_callback signal: {signal} data: {data}")

        if signal == SIGNAL_DATA:
            for key, value in data.items():
                unit = self.units.get(key)
                if unit:
                    self.units[key].process_update(value)
                else:
                    error_msg = 'signalling_callback unit is null!'
                    error_msg += f"signal: {signal} data: {data}"
                    _LOGGER.error(error_msg)
        elif signal == SIGNAL_CONNECTION_STATE and (data == STATE_STOPPED):
            _LOGGER.debug("signalling_callback websocket STATE_STOPPED")

            # Set all units to offline
            self.set_all_units_offline()

            _LOGGER.debug("signalling_callback: creating reconnection")
            self._hass.loop.create_task(self.async_reconnect())
        elif signal == SIGNAL_CONNECTION_STATE \
                and (data == STATE_DISCONNECTED):
            _LOGGER.debug("signalling_callback websocket STATE_DISCONNECTED")

            # Set all units to offline
            self.set_all_units_offline()

            _LOGGER.debug("signalling_callback: creating reconnection")
            self._hass.loop.create_task(self.async_reconnect())
        elif signal == SIGNAL_UNIT_PULL_UPDATE:
            # Update units that is specified
            for unit in data:
                self.update_unit_state(unit)


class CasambiLight(CoordinatorEntity, LightEntity):
    """Defines a Casambi Key Light."""

    def __init__(
            self,
            coordinator,
            idx,
            unit,
            controller,
            hass
    ):
        """Initialize Casambi Key Light."""
        super().__init__(coordinator)
        self.idx = idx
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
        """Return the CT color value in mireds."""
        return self.unit.get_color_temp()

    @property
    def rgb_color(self):
        return self.unit.get_rgb_color()

    @property
    def rgbw_color(self):
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
        """Set color mode for this entity."""
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
        """Flag supported color_modes (in an array format)."""
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
        """Return the state of the light."""
        return bool(self._state)

    def set_online(self, online):
        '''
        Set unit to online
        '''
        self.unit.online = online

        dbg_msg = 'set_online: Setting online to '
        dbg_msg += f"\"{online}\" for unit {self}"
        _LOGGER.debug(dbg_msg)

        if self.enabled:
            # Device needs to be enabled for us to schedule updates
            self.async_schedule_update_ha_state(True)

    def update_state(self):
        '''
        Update units state
        '''
        if self.enabled:
            # Device needs to be enabled for us to schedule updates
            self.async_schedule_update_ha_state(True)

    def process_update(self, data):
        """Process callback message, update home assistant light state"""
        _LOGGER.debug(f"process_update: self: {self} data: {data}")

        if self.enabled:
            # Device needs to be enabled for us to schedule updates
            self.async_schedule_update_ha_state(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        '''
        Turn light off
        '''
        _LOGGER.debug(f"async_turn_off {self}")

        await self.unit.turn_unit_off()

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the light."""
        _LOGGER.debug(
            f"async_turn_on {self} unit: {self.unit} kwargs: {kwargs}")
        brightness = 255

        if ATTR_COLOR_TEMP in kwargs:
            dbg_msg = 'async_turn_on: ATTR_COLOR_TEMP:'
            dbg_msg += f" {kwargs[ATTR_COLOR_TEMP]}"
            _LOGGER.debug(dbg_msg)

            color_temp = kwargs[ATTR_COLOR_TEMP]

            dbg_msg = 'async_turn_on:'
            dbg_msg += f"setting unit color name={self.name}"
            dbg_msg += f" color_temp={color_temp}"
            _LOGGER.debug(dbg_msg)

            await self.unit.set_unit_color_temperature(
                value=color_temp,
                source='mired'
            )

            return

        if ATTR_RGBW_COLOR in kwargs:
            (red, green, blue, white) = kwargs[ATTR_RGBW_COLOR]

            dbg_msg = 'async_turn_on:'
            dbg_msg += f"setting unit color name={self.name}"
            dbg_msg += f" rgbw=({red}, {green}, {blue}, {white})"
            _LOGGER.debug(dbg_msg)

            await self.unit.set_unit_rgbw(
                color_value=(red, green, blue, white),
            )

            return

        if ATTR_RGB_COLOR in kwargs:
            (red, green, blue) = kwargs[ATTR_RGB_COLOR]

            dbg_msg = 'async_turn_on:'
            dbg_msg += f"setting unit color name={self.name}"
            dbg_msg += f" rgb=({red}, {green}, {blue})"
            _LOGGER.debug(dbg_msg)

            await self.unit.set_unit_rgb(
                color_value=(red, green, blue),
                send_rgb_format=True
            )

            return

        if ATTR_BRIGHTNESS in kwargs:
            brightness = round((kwargs[ATTR_BRIGHTNESS] / 255.0), 2)

        if brightness == 255:
            dbg_msg = 'async_turn_on:'
            dbg_msg += f"turning unit on name={self.name}"
            _LOGGER.debug(dbg_msg)

            await self.unit.turn_unit_on()
        else:
            dbg_msg = 'async_turn_on:'
            dbg_msg += f"setting units brightness name={self.name}"
            dbg_msg += f" brightness={brightness}"
            _LOGGER.debug(dbg_msg)

            await self.unit.set_unit_value(value=brightness)

    @property
    def should_poll(self):
        """Disable polling by returning False"""
        return False

    async def async_update(self) -> None:
        """Update Casambi entity."""
        if not self.unit.online:
            _LOGGER.info(f"async_update: unit is not online: {self}")
        else:
            if self.unit.value > 0:
                self._state = True
                self._brightness = int(round(self.unit.value * 255))
            else:
                self._state = False
        _LOGGER.debug(f"async_update {self}")

    @property
    def device_info(self) -> Dict[str, Any]:
        """Return device information about this Casambi Key Light."""
        model = 'Casambi'
        manufacturer = 'Casambi'

        if self.unit.fixture_model:
            model = self.unit.fixture_model

        if self.unit.oem:
            manufacturer = self.unit.oem

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
