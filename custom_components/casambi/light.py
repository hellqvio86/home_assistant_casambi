"""
Support for Casambi lights.
For more details about this component, please refer to the documentation at
https://home-assistant.io/components/@todo
"""
import logging
import ssl
import asyncio

from datetime import timedelta
from pprint import pformat
from typing import Any, Dict, Optional

import async_timeout
import aiocasambi

from aiocasambi.consts import (
    SIGNAL_DATA,
    STATE_RUNNING,
    SIGNAL_CONNECTION_STATE,
    STATE_DISCONNECTED,
    STATE_STOPPED,
    SIGNAL_UNIT_PULL_UPDATE,
)

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
    COLOR_MODE_RGBW,
)

try:
    from homeassistant.components.light import ATTR_DISTRIBUTION
except ImportError:
    ATTR_DISTRIBUTION = "distribution"

from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from homeassistant import config_entries, core
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.const import ATTR_NAME
from homeassistant.helpers import aiohttp_client
from homeassistant.const import CONF_EMAIL, CONF_API_KEY, CONF_SCAN_INTERVAL

import voluptuous as vol
from homeassistant.helpers import entity_platform

from .const import (
    DOMAIN,
    CONF_CONTROLLER,
    CONF_USER_PASSWORD,
    CONF_NETWORK_PASSWORD,
    CONF_NETWORK_TIMEOUT,
    ATTR_IDENTIFIERS,
    ATTR_MANUFACTURER,
    ATTR_MODEL,
    DEFAULT_NETWORK_TIMEOUT,
    DEFAULT_POLLING_TIME,
    SERVICE_CASAMBI_LIGHT_TURN_ON,
    MAX_START_UP_TIME,
    ATTR_SERV_BRIGHTNESS,
    ATTR_SERV_DISTRIBUTION,
    ATTR_SERV_ENTITY_ID,
)

from .errors import ConfigurationError

_LOGGER = logging.getLogger(__name__)

CASAMBI_CONTROLLER = None


async def async_setup_entry(
    hass: core.HomeAssistant,
    config_entry: config_entries.ConfigEntry,
    async_add_entities,
):
    """Setup sensors from a config entry created in the integrations UI."""
    config = hass.data[DOMAIN][config_entry.entry_id]
    user_password = None
    if CONF_USER_PASSWORD in config:
        user_password = config[CONF_USER_PASSWORD]
    network_password = None
    if CONF_NETWORK_PASSWORD in config:
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
        dbg_msg = "async_setup_platform CasambiController already created!"
        _LOGGER.debug(dbg_msg)
        return

    hass.data[DOMAIN][CONF_CONTROLLER] = CasambiController(hass)
    casambi_controller = hass.data[DOMAIN][CONF_CONTROLLER]

    if user_password == "":
        user_password = None

    if network_password == "":
        network_password = None

    if not (user_password) and not (network_password):
        raise ConfigurationError(
            f"{CONF_USER_PASSWORD} or {CONF_NETWORK_PASSWORD} must be set in config!"
        )

    controller = aiocasambi.Controller(
        email=email,
        user_password=user_password,
        network_password=network_password,
        api_key=api_key,
        websession=session,
        sslcontext=sslcontext,
        callback=casambi_controller.signalling_callback,
        network_timeout=network_timeout,
    )

    casambi_controller.controller = controller

    try:
        with async_timeout.timeout(MAX_START_UP_TIME):
            await controller.create_session()
            await controller.initialize()
            await controller.start_websockets()

    except aiocasambi.LoginRequired:
        _LOGGER.error("Integrations UI setup: Connected to casambi but couldn't log in")
        return False

    except aiocasambi.Unauthorized:
        _LOGGER.error("Integrations UI setup: Connected to casambi but not registered")
        return False

    except aiocasambi.RequestError as err:
        _LOGGER.error(
            f"Integrations UI setup: Error connecting to the Casambi, caught aiocasambi.RequestError, error message: {str(err)}"
        )
        return False

    except asyncio.TimeoutError:
        _LOGGER.error(
            "Integrations UI setup: Error connecting to the Casambi, caught asyncio.TimeoutError"
        )
        return False

    except aiocasambi.AiocasambiException:
        _LOGGER.error(
            "Integrations UI setup: Unknown Casambi communication error occurred!"
        )
        return False

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
        if not unit.is_light():
            continue

        casambi_light = CasambiLight(
            coordinator, unit.unique_id, unit, controller, hass
        )
        async_add_entities([casambi_light], True)

        casambi_controller.units[casambi_light.unique_id] = casambi_light

    # add entity service to turn on Casambi light
    platform = entity_platform.async_get_current_platform()
    platform.async_register_entity_service(
        SERVICE_CASAMBI_LIGHT_TURN_ON,
        {
            vol.Required(ATTR_BRIGHTNESS): vol.All(
                vol.Coerce(int), vol.Range(min=0, max=255)
            ),
            vol.Optional(ATTR_DISTRIBUTION): vol.All(
                vol.Coerce(int), vol.Range(min=0, max=255)
            ),
        },
        "async_handle_entity_service_light_turn_on",
    )

    return True


async def async_setup_platform(
    hass: HomeAssistant, config: dict, async_add_entities, discovery_info=None
):
    """
    Setup Casambi platform
    """
    user_password = None
    if CONF_USER_PASSWORD in config:
        user_password = config[CONF_USER_PASSWORD]
    network_password = None
    if CONF_NETWORK_PASSWORD in config:
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
        dbg_msg = "async_setup_platform CasambiController already created!"
        _LOGGER.debug(dbg_msg)
        return

    hass.data[DOMAIN][CONF_CONTROLLER] = CasambiController(hass)
    casambi_controller = hass.data[DOMAIN][CONF_CONTROLLER]

    if user_password == "":
        user_password = None

    if network_password == "":
        network_password = None

    if not (user_password) and not (network_password):
        raise ConfigurationError(
            f"{CONF_USER_PASSWORD} or {CONF_NETWORK_PASSWORD} must be set in config!"
        )

    controller = aiocasambi.Controller(
        email=email,
        user_password=user_password,
        network_password=network_password,
        api_key=api_key,
        websession=session,
        sslcontext=sslcontext,
        callback=casambi_controller.signalling_callback,
        network_timeout=network_timeout,
    )

    casambi_controller.controller = controller

    try:
        with async_timeout.timeout(MAX_START_UP_TIME):
            await controller.create_session()
            await controller.initialize()
            await controller.start_websockets()

    except aiocasambi.LoginRequired:
        _LOGGER.error(
            "configuration.yaml setup: Connected to casambi but couldn't log in"
        )
        return False

    except aiocasambi.Unauthorized:
        _LOGGER.error(
            "configuration.yaml setup: Connected to casambi but not registered"
        )
        return False

    except aiocasambi.RequestError as err:
        _LOGGER.error(
            f"configuration.yaml setup: Error connecting to the Casambi, caught aiocasambi.RequestError, error message: {str(err)}"
        )
        return False

    except asyncio.TimeoutError:
        _LOGGER.error(
            "configuration.yaml setup: Error connecting to the Casambi, caught asyncio.TimeoutError"
        )
        return False

    except aiocasambi.AiocasambiException:
        _LOGGER.error(
            "configuration.yaml setup: Unknown Casambi communication error occurred!"
        )
        return False

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
        if not unit.is_light():
            continue

        casambi_light = CasambiLight(
            coordinator, unit.unique_id, unit, controller, hass
        )
        async_add_entities([casambi_light], True)

        casambi_controller.units[casambi_light.unique_id] = casambi_light

    @callback
    async def async_handle_platform_service_light_turn_on(call: ServiceCall) -> None:
        """Handle turn on of Casambi light when setup from yaml."""
        dbg_msg = f"ServiceCall {call.domain}.{call.service}, data: {call.data}"
        _LOGGER.debug(dbg_msg)

        # Check if entities were selected
        if ATTR_SERV_ENTITY_ID not in call.data:
            # service handle currently only supports selection of entities
            dbg_msg = f"ServiceCall {call.domain}.{call.service}: No entity was specified. Please specify entities instead of areas or devices."
            _LOGGER.error(dbg_msg)

            return

        # Get parameters
        _distribution = None
        _brightness = call.data[ATTR_SERV_BRIGHTNESS]
        _entity_ids = call.data[ATTR_SERV_ENTITY_ID]

        dbg_msg = f"ServiceCall {call.domain}.{call.service}: data: {call.data}, brightness: {_brightness}, entity_ids: {_entity_ids}"

        # Check if optional attribute distribution has been set
        if ATTR_SERV_DISTRIBUTION in call.data:
            _distribution = call.data[ATTR_SERV_DISTRIBUTION]
            dbg_msg += f", distribution: {_distribution}"

        _LOGGER.debug(dbg_msg)

        _units = hass.data[DOMAIN]["controller"].units

        for _entity_id in _entity_ids:
            for casambi_light in _units.values():
                if casambi_light.entity_id == _entity_id:
                    # entity found
                    params = {}
                    params["brightness"] = _brightness
                    if _distribution is not None:
                        params["distribution"] = _distribution

                    dbg_msg = f"async_handle_platform_service_light_turn_on: entity found: {_entity_id}, setting params: {params}"
                    _LOGGER.debug(dbg_msg)

                    await casambi_light.async_turn_on(**params)

    # add platform service to turn on Casambi light
    hass.services.async_register(
        DOMAIN,
        SERVICE_CASAMBI_LIGHT_TURN_ON,
        async_handle_platform_service_light_turn_on,
    )

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
        """
        Getter for controller
        """
        return self._controller

    @controller.setter
    def controller(self, controller):
        """
        Setter for controller
        """
        self._controller = controller

    async def async_update_data(self):
        """Function for polling network state (state of lights)"""
        _LOGGER.debug("async_update_data started")
        try:
            await self._controller.get_network_state()
        except aiocasambi.LoginRequired:
            # Need to reconnect, session is invalid
            await self.async_reconnect()

    async def async_reconnect(self):
        """
        Reconnect to the Internet API
        """
        _LOGGER.debug("async_reconnect: trying to connect to casambi")
        await self._controller.reconnect()

        all_running = True
        states = self._controller.get_websocket_states()
        for state in states:
            if state != STATE_RUNNING:
                all_running = False

        if not all_running:
            msg = "async_reconnect: could not connect to casambi. "
            msg += f"trying again in {self._network_retry_timer} seconds"
            _LOGGER.debug(msg)

            # Try again to reconnect
            self._hass.loop.call_later(self._network_retry_timer, self.async_reconnect)

    def update_unit_state(self, unit):
        """
        Update unit state
        """
        _LOGGER.debug(f"update_unit_state: unit: {unit} units: {self.units}")
        if unit in self.units:
            self.units[unit].update_state()

    def update_all_units(self):
        """
        Update all the units state
        """
        for key in self.units:
            self.units[key].update_state()

    def set_all_units_offline(self):
        """
        Set all units to offline
        """
        for key in self.units:
            self.units[key].set_online(False)

    def signalling_callback(self, signal, data):
        """
        Signalling callback
        """

        _LOGGER.debug(f"signalling_callback signal: {signal} data: {data}")

        if signal == SIGNAL_DATA:
            for key, value in data.items():
                unit = self.units.get(key)
                if unit:
                    self.units[key].process_update(value)
                else:
                    warn_msg = "signalling_callback: unit is None!"
                    warn_msg += f"key: {key} signal: {signal} data: {data} "
                    warn_msg += f"units: {pformat(self.units)}"
                    _LOGGER.warning(warn_msg)
        elif signal == SIGNAL_CONNECTION_STATE and (data == STATE_STOPPED):
            _LOGGER.debug("signalling_callback websocket STATE_STOPPED")

            # Set all units to offline
            self.set_all_units_offline()

            _LOGGER.debug("signalling_callback: creating reconnection")
            self._hass.loop.create_task(self.async_reconnect())
        elif signal == SIGNAL_CONNECTION_STATE and (data == STATE_DISCONNECTED):
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

    def __init__(self, coordinator, idx, unit, controller, hass):
        """Initialize Casambi Key Light."""
        super().__init__(coordinator)
        self.idx = idx
        self._brightness: Optional[int] = None
        self._distribution: Optional[int] = None
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
    def distribution(self) -> Optional[int]:
        """Return the distribution of this light between 1..255."""
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

    @property
    def extra_state_attributes(self):  # -> dict[str, str] | None:
        #    """Return the optional state attributes."""
        return {
            "distribution": self._distribution,
        }

    def set_online(self, online):
        """
        Set unit to online
        """
        self.unit.online = online

        dbg_msg = "set_online: Setting online to "
        dbg_msg += f'"{online}" for unit {self}'
        _LOGGER.debug(dbg_msg)

        if self.enabled:
            # Device needs to be enabled for us to schedule updates
            self.async_schedule_update_ha_state(True)

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
                self._distribution = int(round(self.unit.distribution * 255))
            else:
                self._state = False
        _LOGGER.debug(f"async_update {self}")

    @property
    def device_info(self) -> Dict[str, Any]:
        """Return device information about this Casambi Key Light."""
        model = "Casambi"
        manufacturer = "Casambi"

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

    async def async_handle_entity_service_light_turn_on(self, **kwargs: Any) -> None:
        """Handle turn on of Casambi light when setup from UI integration."""
        # Get parameters
        _brightness = kwargs.get(ATTR_SERV_BRIGHTNESS)
        _distribution = kwargs.get(ATTR_SERV_DISTRIBUTION, None)

        dbg_msg = f"async_handle_entity_service_light_turn_on: self: {self}, kwargs: {kwargs}, brightness: {_brightness}, distribution: {_distribution}"
        _LOGGER.debug(dbg_msg)

        params = {}
        params["brightness"] = _brightness
        if _distribution is not None:
            params["distribution"] = _distribution

        dbg_msg = f"async_handle_entity_service_light_turn_on: entity: {self.entity_id}, setting params: {params}"
        _LOGGER.debug(dbg_msg)

        await self.async_turn_on(**params)

    def __repr__(self) -> str:
        """Return the representation."""
        name = self.unit.name

        result = f"<Casambi light {name}: unit={self.unit}"

        return result
