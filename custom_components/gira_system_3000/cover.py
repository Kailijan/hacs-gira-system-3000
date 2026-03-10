"""Cover platform for Gira System 3000 integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.cover import CoverEntity, CoverDeviceClass, CoverEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
import voluptuous as vol

from custom_components.gira_system_3000.const import DATA_KEY_COORDINATOR, DOMAIN
from custom_components.gira_system_3000.coordinator import GiraBleCoordinator

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = {
    # Hier könnten spezifische Konfigurationsoptionen für die Cover-Entitäten definiert werden, z.B.:
    # vol.Optional("cover_name", default="Gira Cover"): str,
}

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up cover entities from config entry."""
    _LOGGER.info("Setting up cover entities for Gira System 3000")
    # Placeholder for cover setup
    coordinator: GiraBleCoordinator = hass.data[DOMAIN][config_entry.entry_id][DATA_KEY_COORDINATOR]
    async_add_entities([GiraBleCover(coordinator)])

class GiraBleCover(CoverEntity):
    _attr_device_class = CoverDeviceClass.BLIND
    _attr_name = "Gira Blind"
    _attr_is_closed = True
    _attr_current_cover_position = 0
    _attr_supported_features = (
        CoverEntityFeature.OPEN
        | CoverEntityFeature.CLOSE
        | CoverEntityFeature.STOP
        | CoverEntityFeature.SET_POSITION
    )

    def __init__(self, coordinator: GiraBleCoordinator):
        super().__init__()
        self._coordinator = coordinator

    async def async_open_cover(self, **kwargs):
        self._coordinator.open_cover()
        self._attr_is_closed = False
        self._attr_current_cover_position = 100
        self.async_write_ha_state()
    
    async def async_close_cover(self, **kwargs):
        self._coordinator.close_cover()
        self._attr_is_closed = True
        self._attr_current_cover_position = 0
        self.async_write_ha_state()

    async def async_stop_cover(self, **kwargs):
        self._coordinator.stop_cover()
        self.async_write_ha_state()

    async def async_set_cover_position(self, **kwargs):
        pos = kwargs.get("position")
        gira_pos = int(100 - pos)
        self._coordinator.set_cover_position(gira_pos)
        self._attr_current_cover_position = pos
        self._attr_is_closed = pos == 0
        self.async_write_ha_state()