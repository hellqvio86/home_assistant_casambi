"""The casambi integration."""
import asyncio
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.issue_registry import async_create_issue, IssueSeverity

from .utils import async_create_controller, async_create_coordinator

from .const import (
    DOMAIN,
    CONF_CONTROLLER,
    CONF_COORDINATOR,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Set up platform from a ConfigEntry."""
    hass.data.setdefault(DOMAIN, {})
    config = hass.data[DOMAIN][config_entry.entry_id] = dict(config_entry.data)
    # Registers update listener to update config entry when options are updated.
    # Store a reference to the unsubscribe function to cleanup if an entry is unloaded.
    config["remove_update_listener"] = config_entry.add_update_listener(
        options_update_listener
    )

    if CONF_CONTROLLER in hass.data[DOMAIN]:
        dbg_msg = "async_setup_platform CasambiController already created!"
        _LOGGER.debug(dbg_msg)

        async_create_issue(
            hass=hass,
            domain=DOMAIN,
            issue_id="restart_required_casambi",
            is_fixable=True,
            issue_domain=DOMAIN,
            severity=IssueSeverity.WARNING,
            translation_key="restart_required",
            translation_placeholders={},
        )
        return True

    controller = hass.data[DOMAIN][CONF_CONTROLLER] = await async_create_controller(
        hass, config
    )
    if not controller:
        return False
    hass.data[DOMAIN][CONF_COORDINATOR] = await async_create_coordinator(
        hass, config, controller
    )

    # Forward the setup to the sensor platform.
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(config_entry, Platform.LIGHT)
    )
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(
            config_entry, Platform.BINARY_SENSOR
        )
    )
    return True


async def options_update_listener(hass: HomeAssistant, config_entry: ConfigEntry):
    """
    Handle options update.
    """
    await hass.config_entries.async_reload(config_entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """
    Unload a config entry.
    """
    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(
                    config_entry, Platform.LIGHT
                ),
                hass.config_entries.async_forward_entry_unload(
                    config_entry, Platform.BINARY_SENSOR
                ),
            ]
        )
    )
    # Remove options_update_listener.
    hass.data[DOMAIN][config_entry.entry_id]["remove_update_listener"]()

    # Remove config entry from domain.
    if unload_ok:
        hass.data[DOMAIN].pop(config_entry.entry_id)

    return unload_ok


async def async_setup(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Set up the GitHub Custom component from yaml configuration."""

    _LOGGER.debug(f"async_setup config_entry: {config_entry}")

    hass.data.setdefault(DOMAIN, {})

    return True
