import logging
from collections.abc import Callable
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from homeassistant.core import HomeAssistant

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
            update_interval=None,  # Push-only updates via BLE notifications
        )
        self._hass = hass
        self._api = api
        self.data = {}
        self._callbacks: list[Callable[[], None]] = []
        # Register the cover position notification handler with the API.
        self._api.set_cover_position_callback(self.cover_position_notification_handler)

    def register_callback(self, callback: Callable[[], None]) -> None:
        """Register a callback to be invoked when new data arrives."""
        self._callbacks.append(callback)

    def remove_callback(self, callback: Callable[[], None]) -> None:
        """Remove a previously registered callback."""
        try:
            self._callbacks.remove(callback)
        except ValueError:
            _LOGGER.debug("Attempted to remove an unregistered callback: %s", callback)

    def notify_listeners(self) -> None:
        """Notify all registered callbacks about updated data."""
        for callback in self._callbacks:
            callback()

    def open_cover(self):
        self._api.send_command_up()
    
    def close_cover(self):
        self._api.send_command_down()
    
    def stop_cover(self):
        self._api.send_command_stop()

    def set_cover_position(self, position: int):
        self._api.send_command(position)

    def cover_position_notification_handler(self, handle, data: bytearray) -> None:
        """Handle incoming cover position notifications from the BLE device.
        
        The last byte of the payload encodes the position:
          0x00 = fully open, 0xFF = fully closed.
        This is converted to the Home Assistant convention where
          0 = fully closed and 100 = fully open.
        """
        if not data:
            _LOGGER.warning("Received empty cover position notification")
            return
        _LOGGER.debug("Received cover position notification: %s", data.hex())
        raw_value = data[-1]
        # Convert BLE range (0=open, 255=closed) to HA range (0=closed, 100=open).
        # Integer arithmetic avoids floating-point rounding surprises.
        ha_position = (255 - raw_value) * 100 // 255
        self.data["cover_position"] = ha_position
        self.notify_listeners()

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