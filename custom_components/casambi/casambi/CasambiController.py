"""
Support for Casambi lights.
"""
import logging

from pprint import pformat

import aiocasambi

from aiocasambi.consts import (
    SIGNAL_DATA,
    STATE_RUNNING,
    SIGNAL_CONNECTION_STATE,
    STATE_DISCONNECTED,
    STATE_STOPPED,
    SIGNAL_UNIT_PULL_UPDATE,
)


_LOGGER = logging.getLogger(__name__)


class CasambiController:
    """Manages a single Casambi Controller."""

    def __init__(self, hass, network_retry_timer=30, units={}):
        """Initialize the system."""
        self._hass = hass
        self._controller = None
        self._network_retry_timer = network_retry_timer
        self.units = units
        self.entities = []

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
        for entity in self.entities:
            if entity._unit_unique_id == unit:
                entity.update_state()

    def update_all_units(self):
        """
        Update all the units state
        """
        for entity in self.entities:
            entity.update_state()

    def set_all_units_offline(self):
        """
        Set all units to offline
        """
        for entity in self.entities:
            entity.set_online(False)

    def signalling_callback(self, signal, data):
        """
        Signalling callback
        """

        _LOGGER.debug(f"signalling_callback signal: {signal} data: {data}")

        if signal == SIGNAL_DATA:
            for entity in self.entities:
                entity.process_update(data)
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
