"""The Deye SUN Inverter integration."""
from __future__ import annotations

import asyncio
import logging
import re
from datetime import timedelta, datetime
from typing import Any

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DOMAIN,
    CONF_HOST,
    CONF_USERNAME,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    WIFI_UPDATE_INTERVAL,
    DEVICE_INFO_UPDATE_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Deye SUN Inverter from a config entry."""
    host = entry.data[CONF_HOST]
    username = entry.data[CONF_USERNAME]
    password = entry.data[CONF_PASSWORD]
    scan_interval = entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

    coordinator = DeyeDataUpdateCoordinator(
        hass,
        host=host,
        username=username,
        password=password,
        scan_interval=scan_interval,
    )

    # First refresh - don't fail if inverter is offline (e.g., at night)
    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception as err:
        _LOGGER.warning(
            "Initial connection to inverter failed (might be offline/night mode): %s",
            err
        )
        # Set initial empty data so sensors show as unavailable but integration loads
        coordinator.data = coordinator._get_empty_data()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Register update listener for config changes
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


class DeyeDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Deye inverter data."""

    def __init__(
        self,
        hass: HomeAssistant,
        host: str,
        username: str,
        password: str,
        scan_interval: int,
    ) -> None:
        """Initialize the coordinator."""
        _LOGGER.info(
            "Initializing Deye coordinator for %s with %ds update interval",
            host, scan_interval
        )
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )
        self.host = host
        self.username = username
        self.password = password
        self._session = async_get_clientsession(hass)
        
        # Track last update times for different data types
        self._last_wifi_update: datetime | None = None
        self._last_device_info_update: datetime | None = None
        
        # Cache for device info (only fetched once per day)
        self._device_info_cache: dict[str, Any] = {}
        
        # Cache for wifi info (fetched every 15 minutes)
        self._wifi_info_cache: dict[str, Any] = {}
        
        # Cache for energy values (preserved when offline)
        self._energy_cache: dict[str, Any] = {
            "today_energy": 0.0,
            "total_energy": 0.0,
            "current_power": 0.0,
        }
        
        # Track connection state
        self._is_available = False
        self._consecutive_failures = 0
        self._max_failures_before_unavailable = 3

    def _get_empty_data(self) -> dict:
        """Return data structure when inverter is unavailable (night mode)."""
        return {
            # Power data - 0 when offline (no production)
            "current_power": 0.0,
            # Energy data - use cached values to preserve dashboard calculations
            "today_energy": self._energy_cache.get("today_energy", 0.0),
            "total_energy": self._energy_cache.get("total_energy", 0.0),
            # Device info - use cached values
            "serial_number": self._device_info_cache.get("serial_number"),
            "firmware_version": self._device_info_cache.get("firmware_version"),
            # WiFi info - None when offline (will show "Offline")
            "wifi_ssid": None,
            "wifi_signal": None,
            # Availability flag
            "available": False,
        }

    async def _async_update_data(self) -> dict:
        """Fetch data from the Deye inverter web interface."""
        url = f"http://{self.host}/status.html"
        
        try:
            auth = aiohttp.BasicAuth(self.username, self.password)
            # Reduce timeout to prevent overlapping with scan interval
            # Deye inverters are slow single-threaded devices. 
            # If it takes >10s, it's likely stuck or busy.
            timeout = aiohttp.ClientTimeout(total=10, connect=5)
            
            async with self._session.get(url, auth=auth, timeout=timeout) as response:
                if response.status == 401:
                    _LOGGER.error("Authentication failed - check username and password")
                    self._consecutive_failures += 1
                    return self._handle_failure("Authentication failed")
                
                if response.status != 200:
                    _LOGGER.warning("HTTP error %s from inverter", response.status)
                    self._consecutive_failures += 1
                    return self._handle_failure(f"HTTP error {response.status}")
                
                html = await response.text()
                
                # Reset failure counter on success
                self._consecutive_failures = 0
                self._is_available = True
                
                return self._parse_status_page(html)
                
        except asyncio.TimeoutError:
            _LOGGER.debug("Timeout connecting to inverter (might be offline/night)")
            self._consecutive_failures += 1
            return self._handle_failure("Connection timeout")
            
        except aiohttp.ClientConnectorError as err:
            _LOGGER.debug("Cannot connect to inverter (might be offline/night): %s", err)
            self._consecutive_failures += 1
            return self._handle_failure("Connection refused")
            
        except aiohttp.ClientError as err:
            _LOGGER.warning("Error communicating with inverter: %s", err)
            self._consecutive_failures += 1
            return self._handle_failure(str(err))
            
        except Exception as err:
            _LOGGER.exception("Unexpected error fetching inverter data")
            self._consecutive_failures += 1
            return self._handle_failure(str(err))

    def _handle_failure(self, reason: str) -> dict:
        """Handle connection failure gracefully."""
        # Only mark as unavailable after multiple consecutive failures
        if self._consecutive_failures >= self._max_failures_before_unavailable:
            self._is_available = False
            _LOGGER.info(
                "Inverter marked as unavailable after %d failures (reason: %s)",
                self._consecutive_failures,
                reason
            )
            # When truly unavailable (night mode), power is 0
            return self._get_empty_data()
        else:
            _LOGGER.debug(
                "Connection failed (%d/%d): %s",
                self._consecutive_failures,
                self._max_failures_before_unavailable,
                reason
            )
            # For short glitches, return last known good values including power
            # This prevents power drops to 0 during short network issues
            return {
                "current_power": self._energy_cache.get("current_power", 0.0),
                "today_energy": self._energy_cache.get("today_energy", 0.0),
                "total_energy": self._energy_cache.get("total_energy", 0.0),
                "serial_number": self._device_info_cache.get("serial_number"),
                "firmware_version": self._device_info_cache.get("firmware_version"),
                "wifi_ssid": self._wifi_info_cache.get("wifi_ssid"),
                "wifi_signal": self._wifi_info_cache.get("wifi_signal"),
                "available": True, # Pretend to be available during glitches
            }

    def _should_update_wifi(self) -> bool:
        """Check if WiFi info should be updated (every 15 minutes)."""
        if self._last_wifi_update is None:
            return True
        elapsed = (datetime.now() - self._last_wifi_update).total_seconds()
        return elapsed >= WIFI_UPDATE_INTERVAL

    def _should_update_device_info(self) -> bool:
        """Check if device info should be updated (once per day)."""
        if self._last_device_info_update is None:
            return True
        elapsed = (datetime.now() - self._last_device_info_update).total_seconds()
        return elapsed >= DEVICE_INFO_UPDATE_INTERVAL

    def _parse_status_page(self, html: str) -> dict:
        """Parse the status.html page and extract sensor values from JavaScript variables."""
        data: dict[str, Any] = {"available": True}
        
        # === POWER DATA (always updated) ===
        
        # Current power (W)
        match = re.search(r'var\s+webdata_now_p\s*=\s*"([^"]*)";', html)
        if match:
            data["current_power"] = self._parse_numeric_value(match.group(1))
        else:
            # If parsing fails, use last known value instead of 0 to avoid drops
            data["current_power"] = self._energy_cache.get("current_power", 0.0)
            _LOGGER.debug("webdata_now_p not found, using cached value")
        
        # Today's energy (kWh)
        match = re.search(r'var\s+webdata_today_e\s*=\s*"([^"]*)";', html)
        if match:
            new_today = self._parse_numeric_value(match.group(1))
            if new_today > 0:
                data["today_energy"] = new_today
            else:
                # If parsing returned 0 (error/glitch), keep cached value
                data["today_energy"] = self._energy_cache.get("today_energy", 0.0)
        else:
            data["today_energy"] = self._energy_cache.get("today_energy", 0.0)
            _LOGGER.debug("webdata_today_e not found, using cached value")
        
        # Total energy (kWh)
        match = re.search(r'var\s+webdata_total_e\s*=\s*"([^"]*)";', html)
        if match:
            new_total = self._parse_numeric_value(match.group(1))
            if new_total > 0:
                data["total_energy"] = new_total
            else:
                # If parsing returned 0 (error/glitch), keep cached value
                data["total_energy"] = self._energy_cache.get("total_energy", 0.0)
        else:
            # Keep last known value for total energy
            data["total_energy"] = self._energy_cache.get("total_energy", 0.0)
            _LOGGER.debug("webdata_total_e not found, using cached value")
        
        # Update energy cache with new values (for use when offline)
        self._energy_cache["current_power"] = data.get("current_power", 0.0)
        
        # Only update energy caches if we have valid values
        if data.get("today_energy", 0.0) > 0:
            self._energy_cache["today_energy"] = data.get("today_energy", 0.0)
        
        # Only update total energy cache if we have a valid value
        if data.get("total_energy", 0.0) > 0:
            self._energy_cache["total_energy"] = data.get("total_energy", 0.0)
        
        # === WIFI DATA (updated every 15 minutes) ===
        
        if self._should_update_wifi():
            _LOGGER.debug("Updating WiFi information")
            
            # WiFi SSID
            match = re.search(r'var\s+cover_sta_ssid\s*=\s*"([^"]*)";', html)
            if match:
                self._wifi_info_cache["wifi_ssid"] = match.group(1).strip()
            
            # WiFi Signal strength
            match = re.search(r'var\s+cover_sta_rssi\s*=\s*"([^"]*)";', html)
            if match:
                self._wifi_info_cache["wifi_signal"] = match.group(1).strip()
            
            self._last_wifi_update = datetime.now()
        
        # Add cached WiFi data
        data["wifi_ssid"] = self._wifi_info_cache.get("wifi_ssid")
        data["wifi_signal"] = self._wifi_info_cache.get("wifi_signal")
        
        # === DEVICE INFO (updated once per day) ===
        
        if self._should_update_device_info():
            _LOGGER.debug("Updating device information")
            
            # Serial number
            match = re.search(r'var\s+webdata_sn\s*=\s*"([^"]*)";', html)
            if match:
                self._device_info_cache["serial_number"] = match.group(1).strip()
            
            # Firmware version
            match = re.search(r'var\s+cover_ver\s*=\s*"([^"]*)";', html)
            if match:
                self._device_info_cache["firmware_version"] = match.group(1).strip()
            
            # Module ID
            match = re.search(r'var\s+cover_mid\s*=\s*"([^"]*)";', html)
            if match:
                self._device_info_cache["module_id"] = match.group(1).strip()
            
            self._last_device_info_update = datetime.now()
        
        # Add cached device data
        data["serial_number"] = self._device_info_cache.get("serial_number")
        data["firmware_version"] = self._device_info_cache.get("firmware_version")
        data["module_id"] = self._device_info_cache.get("module_id")
        
        _LOGGER.debug("Parsed data: power=%s W, today=%s kWh, total=%s kWh",
                      data.get("current_power"), data.get("today_energy"), data.get("total_energy"))
        
        return data

    def _parse_numeric_value(self, text: str) -> float:
        """Parse numeric value from text. Returns 0.0 on failure."""
        try:
            value = text.strip()
            if not value or value == "---" or value == "":
                return 0.0
            return float(value)
        except (ValueError, AttributeError) as err:
            _LOGGER.debug("Could not parse numeric value '%s': %s", text, err)
            return 0.0

    @property
    def is_inverter_available(self) -> bool:
        """Return True if the inverter is currently reachable."""
        return self._is_available
