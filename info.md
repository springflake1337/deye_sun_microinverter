# Deye SUN Micro-Inverter - Home Assistant Integration

A local Home Assistant integration for Deye SUN micro-inverters (SUN600, SUN800, SUN1000, etc.). Reads real-time data directly from the inverter's web interface.

## Features ⭐

- **Real-time Sensors:** Current power, today's energy, total energy
- **Diagnostic Sensors:** WiFi info (SSID, signal), serial number, firmware, status
- **Energy Dashboard:** Full compatibility with HA Energy Dashboard
- **Night Mode:** No "unavailable" errors - sensors stay available at night
- **Configurable:** Adjustable update intervals (10-3600 seconds)
- **Multi-Device:** Monitor multiple inverters simultaneously
- **Local:** Works completely without internet in local network

## Installation

**Via HACS:**
1. Open HACS → Integrations
2. 3-dot menu → "Custom Repositories"
3. Add repository: `https://github.com/springflake1337/deye_sun_microinverter`
4. Category: Integration
5. Install & Restart Home Assistant

**Manual:**
```bash
cp -r custom_components/deye_sun_microinverter ~/.homeassistant/custom_components/
# Then restart Home Assistant
```

## Quick Start

1. **Settings** → **Devices & Services** → **+ Create Integration**
2. Search for "Deye SUN"
3. Enter IP address, username, password
4. Sensors appear automatically

## Supported Models

- Deye SUN600
- Deye SUN800 ✅ (tested)
- Deye SUN1000
- Other models with same web interface

## Requirements

- Home Assistant 2023.6+
- Python 3.10+
- Local network connection
- Static IP for inverter (important!)

## Documentation

See **README.md** for detailed guide, troubleshooting, and dashboard examples.

---

**MIT License** | Developed for Home Assistant Community
