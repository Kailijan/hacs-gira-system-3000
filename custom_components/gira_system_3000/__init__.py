"""The Gira System 3000 integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ADDRESS, Platform
from homeassistant.core import HomeAssistant

from custom_components.gira_system_3000.api import GiraBleApi
from custom_components.gira_system_3000.coordinator import GiraBleCoordinator

from .const import DATA_KEY_API, DATA_KEY_COORDINATOR, DOMAIN

_LOGGER = logging.getLogger(__name__)


PLATFORMS = [Platform.COVER]#, Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Gira System 3000 from a config entry."""
    _LOGGER.info("Setting up Gira System 3000 integration")

    address: str = entry.data[CONF_ADDRESS]
    
    api = GiraBleApi(hass, address)
    coordinator = GiraBleCoordinator(hass, api)
    
    # Save coordinator and API for later use
    hass.data.setdefault(DOMAIN, {})
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        DATA_KEY_COORDINATOR: coordinator,
        DATA_KEY_API: api,
    }
    
    # Setup platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(
        entry, PLATFORMS
    ):
        entry_data = hass.data[DOMAIN].pop(entry.entry_id)
        del entry_data[DATA_KEY_API]

    return unload_ok
