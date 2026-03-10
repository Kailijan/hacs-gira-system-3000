from datetime import timedelta
import logging
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
)

from custom_components.gira_system_3000.api import GiraBleApi


_LOGGER = logging.getLogger(__name__)

# async def async_setup_entry(hass, config_entry):
#     """Set up the Gira BLE Coordinator."""
#     address = config_entry.data[CONF_ADDRESS]
#     coordinator = GiraBLECoordinator(hass, address)
#     config_entry.runtime_data["coordinator"] = coordinator

class GiraBleCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, api: GiraBleApi):
        super().__init__(
            hass,
            _LOGGER,
            name="Gira BLE Coordinator",
            update_interval=timedelta(seconds=60),  # Wir aktualisieren nur bei Benachrichtigungen
        )
        self._hass = hass
        self._api = api

    def open_cover(self):
        self._api.send_command_up()
    
    def close_cover(self):
        self._api.send_command_down()
    
    def stop_cover(self):
        self._api.send_command_stop()

    def set_cover_position(self, position: int):
        self._api.send_command(position)

    def notification_handler(self, handle, data):
        """Zentrale Verarbeitung der eingehenden Bluetooth-Bytes."""
        _LOGGER.info("Received update: %s", data.hex())
        if data[0] == 0xfb and data[4] == 0x0b:
            # Parsing der Sensordaten
            temp = data[8]
            lux_raw = (data[9] << 8) | data[10]
            lux = round(lux_raw * 3.68)
            
            # Daten im Coordinator speichern
            self.data["temperature"] = temp
            self.data["brightness"] = lux
            
            # Alle registrierten Entitäten (Sensoren) informieren
            self.notify_listeners()