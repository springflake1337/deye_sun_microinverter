"""Sensor platform for Deye SUN Inverter integration."""
from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfEnergy,
    UnitOfPower,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.restore_state import RestoreEntity

from . import DeyeDataUpdateCoordinator
from .const import DOMAIN, CONF_HOST


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Deye SUN Inverter sensors based on a config entry."""
    coordinator: DeyeDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    host = entry.data[CONF_HOST]

    sensors = [
        # Power sensors (always updated)
        DeyeCurrentPowerSensor(coordinator, host),
        DeyeTodayEnergySensor(coordinator, host),
        DeyeTotalEnergySensor(coordinator, host),
        # WiFi sensors (updated every 15 minutes)
        DeyeWifiSsidSensor(coordinator, host),
        DeyeWifiSignalSensor(coordinator, host),
        # Device info sensors (updated once per day)
        DeyeSerialNumberSensor(coordinator, host),
        DeyeFirmwareVersionSensor(coordinator, host),
        # Status sensor
        DeyeStatusSensor(coordinator, host),
    ]

    async_add_entities(sensors)


class DeyeBaseSensor(CoordinatorEntity[DeyeDataUpdateCoordinator], SensorEntity):
    """Base class for Deye sensors."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: DeyeDataUpdateCoordinator,
        host: str,
        name: str,
        key: str,
        icon: str,
        device_class: SensorDeviceClass | None = None,
        state_class: SensorStateClass | None = None,
        unit: str | None = None,
        entity_category: str | None = None,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = name
        self._key = key
        self._attr_icon = icon
        self._attr_unique_id = f"deye_inverter_{host}_{key}"
        self._host = host
        
        if device_class:
            self._attr_device_class = device_class
        if state_class:
            self._attr_state_class = state_class
        if unit:
            self._attr_native_unit_of_measurement = unit
        if entity_category:
            self._attr_entity_category = EntityCategory(entity_category)

        # Device info for grouping sensors
        self._attr_device_info = {
            "identifiers": {(DOMAIN, host)},
            "name": f"Deye Micro-Inverter",
            "manufacturer": "Deye",
            "model": "SUN Series Micro-Inverter",
            "configuration_url": f"http://{host}/",
        }

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get(self._key)

    @property
    def available(self) -> bool:
        """Return True - sensors are always available to preserve dashboard calculations."""
        # Always return True to prevent "unavailable" state which breaks dashboards
        return True

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return additional state attributes."""
        if self.coordinator.data is None:
            return None
        
        # Only add attributes for the main power sensor
        if self._key == "current_power":
            return {
                "inverter_online": self.coordinator.data.get("available", False),
            }
        
        return None


class DeyeCurrentPowerSensor(DeyeBaseSensor):
    """Sensor for current power generation."""

    def __init__(self, coordinator: DeyeDataUpdateCoordinator, host: str) -> None:
        """Initialize the current power sensor."""
        super().__init__(
            coordinator=coordinator,
            host=host,
            name="Aktuelle Leistung",
            key="current_power",
            icon="mdi:solar-power",
            device_class=SensorDeviceClass.POWER,
            state_class=SensorStateClass.MEASUREMENT,
            unit=UnitOfPower.WATT,
        )

    @property
    def native_value(self) -> float:
        """Return 0 when offline (no power production at night)."""
        if self.coordinator.data is None:
            return 0.0
        value = self.coordinator.data.get(self._key)
        if value is None:
            return 0.0
        return float(value)


class DeyeTodayEnergySensor(DeyeBaseSensor, RestoreEntity):
    """Sensor for today's energy generation."""

    def __init__(self, coordinator: DeyeDataUpdateCoordinator, host: str) -> None:
        """Initialize the today's energy sensor."""
        super().__init__(
            coordinator=coordinator,
            host=host,
            name="Energie Heute",
            key="today_energy",
            icon="mdi:solar-power-variant",
            device_class=SensorDeviceClass.ENERGY,
            state_class=SensorStateClass.TOTAL_INCREASING,
            unit=UnitOfEnergy.KILO_WATT_HOUR,
        )
        self._last_known_value = None

    async def async_added_to_hass(self) -> None:
        """Handle entity which will be added."""
        await super().async_added_to_hass()
        if (last_state := await self.async_get_last_state()) is not None:
            try:
                self._last_known_value = float(last_state.state)
            except ValueError:
                pass

    @property
    def native_value(self) -> float:
        """Return cached value when offline to preserve dashboard calculations."""
        val = 0.0
        if self.coordinator.data is not None:
            val = self.coordinator.data.get(self._key, 0.0)
        
        # If we have a valid value from coordinator, use it and update last known
        if val > 0:
            self._last_known_value = val
            return val
        
        # If coordinator has 0 (offline/restart), return last known value
        if self._last_known_value is not None:
            return self._last_known_value
            
        return 0.0


class DeyeTotalEnergySensor(DeyeBaseSensor, RestoreEntity):
    """Sensor for total energy generation."""

    def __init__(self, coordinator: DeyeDataUpdateCoordinator, host: str) -> None:
        """Initialize the total energy sensor."""
        super().__init__(
            coordinator=coordinator,
            host=host,
            name="Energie Gesamt",
            key="total_energy",
            icon="mdi:solar-power-variant-outline",
            device_class=SensorDeviceClass.ENERGY,
            state_class=SensorStateClass.TOTAL_INCREASING,
            unit=UnitOfEnergy.KILO_WATT_HOUR,
        )
        self._last_known_value = None

    async def async_added_to_hass(self) -> None:
        """Handle entity which will be added."""
        await super().async_added_to_hass()
        if (last_state := await self.async_get_last_state()) is not None:
            try:
                self._last_known_value = float(last_state.state)
            except ValueError:
                pass

    @property
    def native_value(self) -> float:
        """Return cached value when offline to preserve dashboard calculations."""
        val = 0.0
        if self.coordinator.data is not None:
            val = self.coordinator.data.get(self._key, 0.0)
        
        # If we have a valid value from coordinator, use it and update last known
        if val > 0:
            self._last_known_value = val
            return val
        
        # If coordinator has 0 (offline/restart), return last known value
        if self._last_known_value is not None:
            return self._last_known_value
            
        return 0.0


class DeyeWifiSsidSensor(DeyeBaseSensor):
    """Sensor for WiFi SSID."""

    def __init__(self, coordinator: DeyeDataUpdateCoordinator, host: str) -> None:
        """Initialize the WiFi SSID sensor."""
        super().__init__(
            coordinator=coordinator,
            host=host,
            name="WLAN Netzwerk",
            key="wifi_ssid",
            icon="mdi:wifi",
            entity_category="diagnostic",
        )

    @property
    def native_value(self) -> str:
        """Return 'Offline' when inverter is not connected."""
        if self.coordinator.data is None:
            return "Offline"
        value = self.coordinator.data.get(self._key)
        if value is None:
            return "Offline"
        return str(value)


class DeyeWifiSignalSensor(DeyeBaseSensor):
    """Sensor for WiFi signal strength."""

    def __init__(self, coordinator: DeyeDataUpdateCoordinator, host: str) -> None:
        """Initialize the WiFi signal sensor."""
        super().__init__(
            coordinator=coordinator,
            host=host,
            name="WLAN Signalstärke",
            key="wifi_signal",
            icon="mdi:wifi-strength-3",
            entity_category="diagnostic",
        )

    @property
    def native_value(self) -> str:
        """Return 'Offline' when inverter is not connected."""
        if self.coordinator.data is None:
            return "Offline"
        value = self.coordinator.data.get(self._key)
        if value is None:
            return "Offline"
        return str(value)

    @property
    def icon(self) -> str:
        """Return icon based on signal strength."""
        value = self.native_value
        if value == "Offline" or value is None:
            return "mdi:wifi-strength-off"
        
        try:
            # Parse percentage value like "49%"
            signal = int(value.replace("%", ""))
            if signal >= 75:
                return "mdi:wifi-strength-4"
            elif signal >= 50:
                return "mdi:wifi-strength-3"
            elif signal >= 25:
                return "mdi:wifi-strength-2"
            elif signal > 0:
                return "mdi:wifi-strength-1"
            else:
                return "mdi:wifi-strength-off"
        except (ValueError, AttributeError):
            return "mdi:wifi-strength-alert-outline"


class DeyeSerialNumberSensor(DeyeBaseSensor):
    """Sensor for device serial number."""

    def __init__(self, coordinator: DeyeDataUpdateCoordinator, host: str) -> None:
        """Initialize the serial number sensor."""
        super().__init__(
            coordinator=coordinator,
            host=host,
            name="Seriennummer",
            key="serial_number",
            icon="mdi:identifier",
            entity_category="diagnostic",
        )

    @property
    def native_value(self) -> str | None:
        """Return cached serial number or 'Unbekannt' if never fetched."""
        if self.coordinator.data is None:
            return "Unbekannt"
        value = self.coordinator.data.get(self._key)
        if value is None:
            return "Unbekannt"
        return str(value)


class DeyeFirmwareVersionSensor(DeyeBaseSensor):
    """Sensor for firmware version."""

    def __init__(self, coordinator: DeyeDataUpdateCoordinator, host: str) -> None:
        """Initialize the firmware version sensor."""
        super().__init__(
            coordinator=coordinator,
            host=host,
            name="Firmware Version",
            key="firmware_version",
            icon="mdi:chip",
            entity_category="diagnostic",
        )

    @property
    def native_value(self) -> str | None:
        """Return cached firmware version or 'Unbekannt' if never fetched."""
        if self.coordinator.data is None:
            return "Unbekannt"
        value = self.coordinator.data.get(self._key)
        if value is None:
            return "Unbekannt"
        return str(value)


class DeyeStatusSensor(DeyeBaseSensor):
    """Sensor for inverter online/offline status."""

    def __init__(self, coordinator: DeyeDataUpdateCoordinator, host: str) -> None:
        """Initialize the status sensor."""
        super().__init__(
            coordinator=coordinator,
            host=host,
            name="Status",
            key="available",
            icon="mdi:power-plug",
            entity_category="diagnostic",
        )

    @property
    def native_value(self) -> str:
        """Return the status as a string."""
        if self.coordinator.data is None:
            return "Unbekannt"
        available = self.coordinator.data.get("available", False)
        return "Online" if available else "Offline (Nachtmodus)"

    @property
    def icon(self) -> str:
        """Return icon based on status."""
        if self.coordinator.data is None:
            return "mdi:power-plug-off"
        available = self.coordinator.data.get("available", False)
        return "mdi:power-plug" if available else "mdi:power-plug-off"

    @property
    def available(self) -> bool:
        """Status sensor is always available."""
        return True
