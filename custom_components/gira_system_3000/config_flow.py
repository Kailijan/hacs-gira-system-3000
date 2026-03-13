import voluptuous as vol
from homeassistant import config_entries
from homeassistant.components.bluetooth import async_discovered_service_info
from homeassistant.const import CONF_ADDRESS, CONF_NAME
from homeassistant.helpers.selector import selector

from .const import DOMAIN


class GiraBleConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handles the configuration flow for Gira System 3000, including Bluetooth discovery, manual device selection, and coupling mode setup."""
    VERSION = 1

    def __init__(self):
        super().__init__()
        self._discovery_info = None
        self._pending_address: str | None = None
        self._pending_name: str | None = None

    async def async_step_bluetooth(self, discovery_info):
        """Triggered when HA discovers a Bluetooth device."""
        await self.async_set_unique_id(discovery_info.address)
        self._abort_if_unique_id_configured()

        # Store discovery info for the confirmation step
        self._discovery_info = discovery_info
        return await self.async_step_bluetooth_confirm()

    async def async_step_bluetooth_confirm(self, user_input=None):
        """Confirmation dialog for discovered devices."""
        if not self._discovery_info:
            return self.async_abort(reason="no_devices_found")

        if user_input is not None:
            # User confirmed – proceed to coupling step
            self._pending_address = self._discovery_info.address
            self._pending_name = self._discovery_info.name or "Gira Jalousie"
            return await self.async_step_coupling()

        return self.async_show_form(
            step_id="bluetooth_confirm",
            description_placeholders={"name": self._discovery_info.name or self._discovery_info.address},
        )

    async def async_step_user(self, user_input=None):
        """Manual setup process via 'Add Integration'."""
        errors = {}

        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_ADDRESS])
            self._abort_if_unique_id_configured()

            # Store device data, then proceed to coupling step
            self._pending_address = user_input[CONF_ADDRESS]
            self._pending_name = user_input.get(CONF_NAME, "Gira Jalousie")
            return await self.async_step_coupling()

        # Build a list of discovered BLE devices for the dropdown
        discovery_info = async_discovered_service_info(self.hass)
        device_registry = {
            dev.address: f"{dev.name} ({dev.address})"
            for dev in discovery_info
            if dev.name
        }

        data_schema = vol.Schema({
            vol.Required(CONF_ADDRESS): selector(
                {
                    "select": {
                        "options": [
                            {"value": addr, "label": name}
                            for addr, name in device_registry.items()
                        ]
                    }
                }
            ),
            vol.Optional(CONF_NAME, default="Gira Jalousie"): str,
        })

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )

    async def async_step_coupling(self, user_input=None):
        """Instruct the user to put the device into coupling mode. Creates the config entry after user confirmation."""
        if not self._pending_address:
            return self.async_abort(reason="setup_incomplete")

        if user_input is not None:
            # User confirmed coupling – create the config entry
            return self.async_create_entry(
                title=self._pending_name or "Gira Jalousie",
                data={
                    CONF_ADDRESS: self._pending_address,
                    CONF_NAME: self._pending_name or "Gira Jalousie",
                },
            )

        return self.async_show_form(
            step_id="coupling",
        )