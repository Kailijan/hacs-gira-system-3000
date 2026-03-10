import voluptuous as vol
from homeassistant import config_entries
from homeassistant.components.bluetooth import async_discovered_service_info
from homeassistant.const import CONF_ADDRESS, CONF_NAME
from homeassistant.helpers.selector import selector

from .const import DOMAIN

class GiraBleConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Behandelt den Setup-Prozess für Gira BLE."""
    VERSION = 1

    def __init__(self):
        super().__init__()
        self._discovery_info = None

    async def async_step_bluetooth(self, discovery_info):
        """Wird ausgelöst, wenn HA ein Bluetooth-Gerät entdeckt."""
        await self.async_set_unique_id(discovery_info.address)
        self._abort_if_unique_id_configured()
        
        # Wir speichern die Info für den nächsten Schritt
        self._discovery_info = discovery_info
        return await self.async_step_bluetooth_confirm()

    async def async_step_bluetooth_confirm(self, user_input=None):
        """Bestätigungs-Dialog für entdeckte Geräte."""
        if not self._discovery_info:
            return self.async_abort(reason="no_devices_found")
        
        if user_input is not None:
            return self.async_create_entry(
                title=self._discovery_info.name or "Gira Jalousie",
                data={
                    CONF_ADDRESS: self._discovery_info.address,
                    CONF_NAME: self._discovery_info.name or "Gira Jalousie",
                }
            )

        return self.async_show_form(
            step_id="bluetooth_confirm",
            description_placeholders={"name": self._discovery_info.name or self._discovery_info.address},
        )

    async def async_step_user(self, user_input=None):
        """Manueller Setup-Prozess via 'Integration hinzufügen'."""
        errors = {}
        
        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_ADDRESS])
            self._abort_if_unique_id_configured()
            
            return self.async_create_entry(
                title=user_input.get(CONF_NAME, "Gira Jalousie"),
                data=user_input
            )

        # Liste der entdeckten BLE-Geräte für das Dropdown
        discovery_info = async_discovered_service_info(self.hass)
        device_registry = {
            dev.address: f"{dev.name} ({dev.address})" 
            for dev in discovery_info 
            if dev.name  # Zeige alle Geräte, lasse Benutzer wählen
        }

        # Formular für die manuelle Eingabe
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
            errors=errors
        )