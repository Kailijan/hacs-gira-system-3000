"""Sensor platform for Gira System 3000 integration."""
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import UnitOfTemperature, LIGHT_LUX
from .const import DATA_KEY_COORDINATOR, DOMAIN

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Setup der Sensoren basierend auf dem Config Entry."""
    # Der Coordinator wurde in __init__.py erstellt
    coordinator = hass.data[DOMAIN][config_entry.entry_id][DATA_KEY_COORDINATOR]
    
    async_add_entities([
        GiraBrightnessSensor(coordinator),
        GiraTemperatureSensor(coordinator)
    ])

class GiraSensorBase(SensorEntity):
    """Gemeinsame Basis für Gira Sensoren."""
    _attr_has_entity_name = True
    _attr_should_poll = False  # Wir erhalten Push-Updates via BLE

    def __init__(self, coordinator):
        self.coordinator = coordinator
        self._attr_unique_id = f"{coordinator.address}_{self.__class__.__name__}"
        self._attr_device_info = coordinator.device_info

    async def async_added_to_hass(self):
        """Wenn die Entität hinzugefügt wird, registrieren wir den Callback."""
        self.coordinator.register_callback(self.async_write_ha_state)

    async def async_will_remove_from_hass(self):
        """Callback entfernen beim Löschen."""
        self.coordinator.remove_callback(self.async_write_ha_state)

class GiraBrightnessSensor(GiraSensorBase):
    """Helligkeitssensor Entität."""
    _attr_name = "Helligkeit"
    _attr_device_class = SensorDeviceClass.ILLUMINANCE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = LIGHT_LUX

    @property
    def native_value(self):
        """Gibt den aktuellen Lux-Wert aus dem Coordinator zurück."""
        return self.coordinator.data.get("brightness")

class GiraTemperatureSensor(GiraSensorBase):
    """Temperatursensor Entität."""
    _attr_name = "Temperatur"
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    @property
    def native_value(self):
        """Gibt die aktuelle Temperatur zurück."""
        return self.coordinator.data.get("temperature")