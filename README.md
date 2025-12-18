# Deye SUN Micro-Inverter - Home Assistant Integration

A custom Home Assistant integration that reads data from Deye SUN micro-inverters via the local web interface.

[![Buy Me a Coffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-ffdd00?style=flat-square&logo=buy-me-a-coffee&logoColor=black)](https://buymeacoffee.com/springflake)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2023.6+-blue.svg)](https://www.home-assistant.io/)

**Supported Models:** Deye SUN600, SUN800, SUN1000, and similar models with the same web interface

**Tested with:** Deye SUN800 (MW3_16U_5406_1.62)

---

## Features

### Power Sensors (Real-time)
- ⚡ **Current Power** (W) - Currently generated power output
- 📊 **Energy Today** (kWh) - Energy generated today
- 📈 **Total Energy** (kWh) - Total energy generated

### Diagnostic Sensors
- 📶 **WiFi Network** - Connected WiFi network (Update: every 15 min)
- 📡 **WiFi Signal** - WiFi signal quality in % (Update: every 15 min)
- 🔢 **Serial Number** - Device serial number (Update: once daily)
- 💾 **Firmware Version** - Current firmware (Update: once daily)
- 🟢 **Status** - Online/Offline (Night mode) indicator

### Robustness & Reliability
- 🌙 **Night Mode Handling** - No errors when inverter is offline at night
- 🔄 **Automatic Reconnection** - Automatically reconnects when sun rises
- 💾 **Data Caching** - WiFi/device info cached to reduce queries
- ⏱️ **Configurable Interval** - 10-3600 seconds (default: 30s)
- 🔐 **HTTP Basic Auth** - Secure authentication
- 📱 **Energy Dashboard** - Full compatibility with HA Energy Dashboard

---

## System Requirements

- Home Assistant 2023.6 or higher
- Python 3.10 or higher
- Network connection to Deye inverter
- **⚠️ Static IP address for the inverter** (see below)

---

## ⚠️ Important: Configure Static IP Address

The Deye inverter has DHCP enabled by default ("Obtain an IP address automatically"). This means the IP address may change after a restart!

**You MUST assign a static IP to the inverter:**

### Option 1: In Router (Recommended)
1. Open your router configuration
2. Find the DHCP settings
3. Assign a **static IP reservation** to the inverter based on its MAC address
4. Find the MAC address on the inverter label or in the test script

### Option 2: In Inverter
1. Connect to the inverter's AP (e.g., `AP_xxxxxxxxxx`)
2. Open `http://10.10.100.254` in browser
3. Go to **Quick Set** → **Wireless**
4. Disable "Obtain an IP address automatically"
5. Enter a static IP, subnet mask, gateway, and DNS
6. Save and restart

### Find IP Address
If you don't know the current IP:
- Check your router (DHCP client list)
- Connect to the inverter's AP and check the status page
- Use a network scanner (e.g., `nmap`, Angry IP Scanner)

---

## Quick Start

### 1. Run Test (Recommended!)

Before installing the integration, test the connection using the included test script:

```bash
# Install dependencies
pip install aiohttp

# Test connection (IP address is required!)
python test_connection.py --host 192.168.1.100

# With custom credentials
python test_connection.py --host 192.168.1.100 --user admin --password yourpassword
```

> **Default Credentials:** `admin` / `admin` - Change these for security!

**Successful Test Output:**
```
============================================================
Deye SUN Micro-Inverter Connection Test
============================================================

🔗 Target: http://192.168.1.100/status.html
👤 Username: admin
🔑 Password: *****
⏰ Time: 2025-12-18 14:30:00

📡 Connecting to inverter...
📬 Response status: 200

📊 Parsing inverter data...

  [Device Info]
    ✓ Serial Number: 24062xxxx
    ✓ Firmware: MW3_16U_5406_1.62
    ✓ Module ID: 387764xxxx

  [WiFi Info]
    ✓ SSID: MyWiFi
    ✓ Signal: 49%
    ✓ IP: 192.168.1.100
    ✓ MAC: D4:27:87:2E:B9:42

  [Power Data]
    ✓ Current Power: 399.0 W
    ✓ Today Energy: 0.5 kWh
    ✓ Total Energy: 381.5 kWh

============================================================
📋 Results Summary
============================================================

🟢 Status: ONLINE

✅ Test SUCCESSFUL - All systems operational!
```

### 2. Installation

#### Manual Installation (Standard)

1. **Clone or download repository:**
   ```bash
   cd /path/to/homeassistant/config
   git clone https://github.com/springflake1337/deye_sun_microinverter.git
   ```

2. **Copy folders:**
   ```bash
   # Copy integration
   cp -r deye_sun_microinverter/custom_components/deye_sun_microinverter custom_components/

3. **Restart Home Assistant**

4. **Add Integration:**
   - Go to **Settings** → **Devices & Services**
   - Click **+ Create Integration**
   - Search for **"Deye Sun Mirco-Inverter"**
   - Follow the configuration

#### HACS Installation (Future)

```
1. Open HACS in Home Assistant
2. Click "Integrations"
3. Click 3-dot menu in top right
4. Select "Custom Repositories"
5. Add repository and select Category "Integration"
6. Install "Deye SUN Micro-Inverter"
7. Restart Home Assistant
```

## Available Sensors

The integration creates **8 sensors** automatically:

### Power Sensors (Update: configurable interval)

| Sensor | Entity ID | Unit | Description |
|--------|-----------|------|-------------|
| **Current Power** | `sensor.deye_inverter_<ip>_current_power` | W | Current generation |
| **Current Power** | `sensor.deye_inverter_<ip>_current_power` | W | Current generation |
| **Energy Today** | `sensor.deye_inverter_<ip>_energy_today` | kWh | Today's generation |
| **Total Energy** | `sensor.deye_inverter_<ip>_total_energy` | kWh | Total generation |

### Diagnostic Sensors (Entity Category: diagnostic)

| Sensor | Entity ID | Update Interval | Description |
|--------|-----------|-----------------|-------------|
| **WiFi Network** | `sensor.deye_inverter_<ip>_wifi_network` | 15 Minutes | Connected WiFi |
| **WiFi Signal** | `sensor.deye_inverter_<ip>_wifi_signal` | 15 Minutes | Signal in % |
| **Serial Number** | `sensor.deye_inverter_<ip>_serial_number` | 24 Hours | Device ID |
| **Firmware Version** | `sensor.deye_inverter_<ip>_firmware_version` | 24 Hours | Software Version |
| **Status** | `sensor.deye_inverter_<ip>_status` | Every Update | Online/Offline |

---

## Energy Dashboard Integration

The sensors are fully compatible with Home Assistant Energy Dashboard:

1. Go to **Energy** in main menu
2. Click **Configuration** (gear icon top right)
3. Under **"Solar Production"** click **"Add Solar Production"**
4. Select **"Energy Today"** or **"Total Energy"**
5. Confirm the configuration

**Result:** Your solar generation will be visualized in the Energy Dashboard!

---

## Test Script Usage

The `test_connection.py` script allows you to test the connection without Home Assistant.

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Usage

```bash
# Option 1: Use default values
python test_connection.py

# Option 2: Custom values
python test_connection.py --host 192.168.2.50 --user admin --password yourpassword

# Option 3: Custom port (if not standard)
python test_connection.py --host 192.168.2.50 -u admin -p mypass

# Option 4: Save HTML response (for debugging)
python test_connection.py --save-html
```

### Script Options

```
usage: test_connection.py [-h] [--host HOST] [--user USER] [--password PASSWORD] [--save-html]

Test connection to Deye SUN inverter

options:
  -h, --help              Show help message
  --host, -H HOST         IP address (default: 192.168.2.50)
  --user, -u USER         Username (default: admin)
  --password, -p PASSWORD Password (default: admin)
  --save-html             Save raw HTML response to file for debugging
```

### Debugging with --save-html

If the script fails, you can use `--save-html` to save the raw data:

```bash
python test_connection.py --host 192.168.2.50 --save-html
```

This creates a file like `deye_response_192_168_2_50.html` with the complete HTTP response.

---

## 🌙 Night Mode / Offline Behavior

The Deye SUN inverter **automatically shuts down** when no solar energy is available (night, cloudy, shaded). This is **normal and intended** - the inverter saves energy this way.

### What happens in Home Assistant?

| Situation | Power Sensors | Energy Sensors | Diagnostic Sensors | Status Sensor |
|-----------|---------------|----------------|--------------------|---------------|
| **Day (Online)** | Current Power | Current Values | Current Values | "Online" |
| **Night (Offline)** | **0 W** | **Last Known Value** | "Offline" / "Unknown" | "Offline (Night Mode)" |
| **Sunrise** | Auto Updated | Auto Updated | Auto Updated | "Online" |

### ✅ Energy Dashboard Compatible!

**Important:** All sensors remain **always "available"** - they never show "Unavailable". This is crucial for Home Assistant Energy Dashboard:

- **current_power:** Shows **0 W** when offline (= no production)
- **today_energy:** Shows **last known value** (resets at midnight by inverter)
- **total_energy:** Shows **last known value** (important for `total_increasing` state class!)

This ensures dashboard calculations work continuously - no gaps, no "unavailable" values.

### No Errors in Log!

The integration is designed so **no errors** appear in Home Assistant logs when inverter is offline:

- ✅ Connection timeouts treated as "normal"
- ✅ Only marked unavailable after 3 consecutive failures
- ✅ Debug-level logging for offline events
- ✅ Cached data remains intact

### Technical Details

```python
# Error tolerance logic
max_failures_before_unavailable = 3  # Only after 3 failures mark as "offline"

# Update intervals (reduces load on inverter)
power_data_interval = 30 seconds     # Configurable
wifi_info_interval = 900 seconds     # 15 Minutes
device_info_interval = 86400 seconds # 24 Hours
```

---

## 🐛 Troubleshooting

### Problem: "Connection Failed"

**Possible Causes:**
- Inverter is offline or powered off
- Wrong IP address
- Network firewall blocking connection

**Solution Steps:**
1. Check IP address: `ping inverter ip-address`
2. Open web interface in browser
3. Check your network and firewall rules

### Problem: "Invalid Credentials"

**Possible Causes:**
- Wrong username or password
- Credentials have been changed

**Solution Steps:**
1. Try logging in manually in browser with inverter ip-address
2. Note the correct credentials
3. Use `test_connection.py` with correct credentials
4. Update the integration in Home Assistant

### Problem: "No Data / Values are 0"

**Possible Causes:**
- It's night or no sun exposure
- Inverter has failed
- Solar panels are shaded

**Solution Steps:**
1. Run test script: `python test_connection.py`
2. Check values directly on inverter
3. Wait for sun exposure and test again
4. If problem persists: restart inverter

---

## 📝 Changelog

### Version 1.0.0
- ✅ Initial release
- ✅ Support for Deye SUN 600/800/1000 Micro-Inverters
- ✅ 8 Sensors: Current Power, Energy Today, Total Energy, WiFi, Device Info, Status
- ✅ HTTP Basic Auth Support
- ✅ Configurable Update Intervals
- ✅ German & English UI
- ✅ Energy Dashboard Integration
- ✅ Test Script for Connection Testing

---

## Support

### Frequently Asked Questions (FAQ)

**Q: Which inverters are supported?**
A: Currently Deye SUN600, SUN800, SUN1000. Other models may work with adjustments.

**Q: How often is data updated?**
A: Default every 30 seconds, configurable from 10-3600 seconds.

**Q: Can I monitor multiple inverters?**
A: Yes! You can add the integration multiple times with different IPs.

**Q: Does the integration cause high load?**
A: No, only simple HTTP queries, very low CPU/memory usage.

**Q: Does it work without Internet?**
A: Yes! The integration works completely in local network.

**Q: Can I sync data backwards somehow?**
A: No, this integration is read-only (data retrieval only).

### Support & Bug Reports

1. First test with: `python test_connection.py`
2. Check Home Assistant logs
3. Open issue on GitHub with:
   - Inverter model and firmware version
   - Home Assistant version
   - Relevant logs (without credentials!)
   - Steps to reproduce

---

## File Structure

```
deye_sun_microinverter/
├── README.md                           # This document
├── requirements.txt                    # Python Dependencies
├── test_connection.py                  # Test Script
└── custom_components/
    └── deye_sun/
        ├── __init__.py                 # Main Integration & Data Coordinator
        ├── config_flow.py              # Configuration UI
        ├── sensor.py                   # Sensor Entities
        ├── const.py                    # Constants
        ├── manifest.json               # Integration Metadata
        ├── strings.json                # UI Strings (English)
        └── translations/
            ├── en.json                 # English Translation
            └── de.json                 # German Translation
```

---

## License

MIT License - See LICENSE file for details

---

## 🙏 Credits

- Developed for Home Assistant Community by springflake
- Tested with Deye SUN800 MW3_16U_5406_1.62

---

## Security

⚠️ **Important:**
- Integration stores username and password in Home Assistant config
- Ensure your Home Assistant is properly protected
- Use strong passwords on your inverter
- Communication is unencrypted (HTTP Basic Auth)

---

**Last Updated:** December 2025
**Compatibility:** Home Assistant 2023.6+
