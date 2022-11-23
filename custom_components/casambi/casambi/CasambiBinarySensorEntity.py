import logging

from homeassistant.core import HomeAssistant

# from homeassistant.components.button import ButtonEntity
# from homeassistant.components.select import SelectEntity
# from homeassistant.components.switch import SwitchEntity
from homeassistant.components.binary_sensor import BinarySensorEntity
# from homeassistant.helpers.entity import DeviceInfo, Entity
# from homeassistant.helpers.entity import EntityCategory

from ..const import DOMAIN

from .CasambiEntity import CasambiEntity

_LOGGER = logging.getLogger(__name__)


class CasambiBinarySensorEntity(BinarySensorEntity, CasambiEntity):
    def __init__(self, unit, controller, hass, name_suffix: str = "", icon=None, device_class=None):
    #     self, name_suffix, entry: dict, hass: HomeAssistant, config_entry, icon=None, device_class=None,
    # ):
        _LOGGER.debug(f"Casambi {name_suffix} - init - start")
        self._attr_is_on = False
        self._hass = hass
        self._attr_icon = icon
        self._attr_device_class = device_class
        # hass.data[DOMAIN][config_entry.entry_id]["entities"].append(self)
        # self.updateCasambi(hass.data[DOMAIN][config_entry.entry_id]["camData"])

        CasambiEntity.__init__(self, unit, controller, hass)
        # entry, name_suffix)
        BinarySensorEntity.__init__(self)
        _LOGGER.debug(f"Casambi {name_suffix} - init - end")

    @property
    def state(self):
        return self._attr_state
