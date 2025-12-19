# Changelog

## [1.0.1] - 2025-12-19

### Fixed
- **Zero-Drop / Glitch Protection:** Implemented intelligent caching to prevent power/energy values from dropping to 0 during short network glitches or inverter reboots.
- **Dashboard Stability:** Added `RestoreEntity` support for Energy sensors. Values are now preserved across Home Assistant restarts even if the inverter is offline (night mode).
- **Update Lag:** Reduced HTTP request timeout from 30s to 10s to prevent update intervals from drifting when the inverter is slow to respond.
- **Manifest:** Fixed missing manifest.json issue during project renaming.

### Changed
- **Project Structure:** Renamed integration domain to `deye_sun_microinverter` for better uniqueness.
- **Sponsorship:** Added "Buy Me a Coffee" links and badges to README and GitHub sidebar.

## [1.0.0] - 2025-12-18

### Added
- ✅ Initial release of Deye SUN Inverter Home Assistant integration.
- ✅ Support for Deye SUN600, SUN800, SUN1000 and compatible models.
- ✅ 8 Sensors: Current Power, Today Energy, Total Energy, WiFi SSID, WiFi Signal, Serial Number, Firmware, Status.
- ✅ HTTP Basic Auth support for secure connection.
- ✅ Configurable update intervals (10-3600 seconds).
- ✅ Energy Dashboard integration with `total_increasing` state class.
- ✅ German and English UI translations.
- ✅ Night mode handling - sensors stay available (no "unavailable" state).
- ✅ Data caching for WiFi info (15 min) and device info (24 hours).
- ✅ Energy caching to preserve values during night/offline periods.
- ✅ Multi-device support (configure multiple inverters).
- ✅ Test script for connection validation.

### Features
- **Robust Offline Handling:** Inverter automatically switches off at night - integration handles this gracefully.
- **No Dashboard Breaks:** All sensors remain available with cached values, ensuring Energy Dashboard calculations continue.
- **Intelligent Caching:** Different update intervals for power data (configurable), WiFi info (15 min), and device info (24 hours).
- **Error Tolerance:** Only marks as unavailable after 3 consecutive failures.
- **Local Only:** Works completely in local network without internet.

### Known Issues
- Only tested with Deye SUN800 (MW3_16U_5406_1.62) - other variants may need adjustments.

---

## Contributing

Contributions welcome! Please open an issue or pull request for:
- Bug reports
- New features
- Additional model support
- Translations
