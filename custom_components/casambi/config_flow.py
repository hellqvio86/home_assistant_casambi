from homeassistant import config_entries
from .const import (
    CONFIG_SCHEMA,
    DOMAIN
)


class CasambiFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle Casambi config flow"""

    VERSION = 1

    async def async_step_user(self, info):
        if info is not None:
            pass  # TODO: process info

        return self.async_show_form(
            step_id="user", data_schema=CONFIG_SCHEMA
        )
