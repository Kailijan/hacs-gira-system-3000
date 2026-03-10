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
    _attr_should_poll = False
    _attr_supported_features = (
        CoverEntityFeature.OPEN
        | CoverEntityFeature.CLOSE
        | CoverEntityFeature.STOP
        | CoverEntityFeature.SET_POSITION
    )

    def __init__(self, coordinator: GiraBleCoordinator):
        super().__init__()
        self._coordinator = coordinator

    async def async_added_to_hass(self) -> None:
        """Register callback so the entity updates when cover position notifications arrive."""
        self._coordinator.register_callback(self.async_write_ha_state)

    async def async_will_remove_from_hass(self) -> None:
        """Unregister callback when the entity is removed."""
        self._coordinator.remove_callback(self.async_write_ha_state)

    @property
    def current_cover_position(self) -> int | None:
        """Return the current cover position (0=closed, 100=open)."""
        return self._coordinator.data.get("cover_position")

    @property
    def is_closed(self) -> bool | None:
        """Return True when the cover is fully closed."""
        pos = self.current_cover_position
        if pos is None:
            return None
        return pos == 0

    async def async_open_cover(self, **kwargs):
        self._coordinator.open_cover()
        # Optimistic update until the device confirms via notification
        self._coordinator.data["cover_position"] = 100
        self.async_write_ha_state()

    async def async_close_cover(self, **kwargs):
        self._coordinator.close_cover()
        # Optimistic update until the device confirms via notification
        self._coordinator.data["cover_position"] = 0
        self.async_write_ha_state()

    async def async_stop_cover(self, **kwargs):
        self._coordinator.stop_cover()
        self.async_write_ha_state()

    async def async_set_cover_position(self, **kwargs):
        pos = kwargs.get("position")
        gira_pos = int(100 - pos)
        self._coordinator.set_cover_position(gira_pos)
        # Optimistic update until the device confirms via notification
        self._coordinator.data["cover_position"] = pos
        self.async_write_ha_state()