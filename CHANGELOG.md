# Changelog

## [1.0.0] - 2025-12-18

### Added
- ✅ Initial release of Deye SUN Inverter Home Assistant integration
- ✅ Support for Deye SUN600, SUN800, SUN1000 and compatible models
- ✅ 8 Sensors: Current Power, Today Energy, Total Energy, WiFi SSID, WiFi Signal, Serial Number, Firmware, Status
- ✅ HTTP Basic Auth support for secure connection
- ✅ Configurable update intervals (10-3600 seconds)
- ✅ Energy Dashboard integration with total_increasing state class
- ✅ German and English UI translations
- ✅ Night mode handling - sensors stay available (no "unavailable" state)
- ✅ Data caching for WiFi info (15 min) and device info (24 hours)
- ✅ Energy caching to preserve values during night/offline periods
- ✅ Multi-device support (configure multiple inverters)
- ✅ Test script for connection validation

### Features
- **Robust Offline Handling:** Inverter automatically switches off at night - integration handles this gracefully
- **No Dashboard Breaks:** All sensors remain available with cached values, ensuring Energy Dashboard calculations continue
- **Intelligent Caching:** Different update intervals for power data (configurable), WiFi info (15 min), and device info (24 hours)
- **Error Tolerance:** Only marks as unavailable after 3 consecutive failures
- **Local Only:** Works completely in local network without internet

### Known Issues
- Only tested with Deye SUN800 (MW3_16U_5406_1.62) - other variants may need adjustments

---

## Contributing

Contributions welcome! Please open an issue or pull request for:
- Bug reports
- New features
- Additional model support
- Translations
