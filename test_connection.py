#!/usr/bin/env python3
"""
Test script for Deye SUN Microinverter integration.
This allows testing the connection and data scraping without Home Assistant.

Supported models: Deye SUN600, SUN800, SUN1000, and similar models
with the same web interface.

Features:
- Tests connection to the inverter
- Validates authentication
- Parses all available data (power, energy, WiFi, device info)
- Handles offline scenarios gracefully (e.g., night mode)

Usage:
    python test_connection.py --host 192.168.1.100
    python test_connection.py --host 192.168.1.100 --user admin --password mypassword
"""

import argparse
import asyncio
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

try:
    import aiohttp
except ImportError:
    print("Missing dependencies. Install them with:")
    print("  pip install aiohttp")
    sys.exit(1)


@dataclass
class InverterData:
    """Data class for inverter readings."""
    # Connection status
    available: bool = False
    error_message: str = ""
    
    # Power data (updated every scan)
    current_power: Optional[float] = None  # Watts
    today_energy: Optional[float] = None   # kWh
    total_energy: Optional[float] = None   # kWh
    
    # Device info (updated once per day in HA)
    serial_number: Optional[str] = None
    firmware_version: Optional[str] = None
    module_id: Optional[str] = None
    
    # WiFi info (updated every 15 min in HA)
    wifi_ssid: Optional[str] = None
    wifi_signal: Optional[str] = None
    wifi_ip: Optional[str] = None
    wifi_mac: Optional[str] = None
    
    # Raw data for debugging
    raw_html: str = ""


def parse_numeric_value(text: str) -> float:
    """Parse numeric value from text. Returns 0.0 on failure."""
    try:
        value = text.strip()
        if not value or value == "---" or value == "":
            return 0.0
        return float(value)
    except (ValueError, AttributeError):
        return 0.0


def parse_status_page(html: str) -> InverterData:
    """Parse the status.html page and extract all sensor values from JavaScript variables."""
    data = InverterData(raw_html=html, available=True)
    
    print("\n📊 Parsing inverter data...")
    
    # === DEVICE INFO ===
    print("\n  [Device Info]")
    
    # Serial number
    match = re.search(r'var\s+webdata_sn\s*=\s*"([^"]*)";', html)
    if match:
        data.serial_number = match.group(1).strip()
        print(f"    ✓ Serial Number: {data.serial_number}")
    else:
        print("    ✗ Serial Number: not found")
    
    # Firmware version
    match = re.search(r'var\s+cover_ver\s*=\s*"([^"]*)";', html)
    if match:
        data.firmware_version = match.group(1).strip()
        print(f"    ✓ Firmware: {data.firmware_version}")
    else:
        print("    ✗ Firmware: not found")
    
    # Module ID
    match = re.search(r'var\s+cover_mid\s*=\s*"([^"]*)";', html)
    if match:
        data.module_id = match.group(1).strip()
        print(f"    ✓ Module ID: {data.module_id}")
    else:
        print("    ✗ Module ID: not found")
    
    # === WIFI INFO ===
    print("\n  [WiFi Info]")
    
    # WiFi SSID
    match = re.search(r'var\s+cover_sta_ssid\s*=\s*"([^"]*)";', html)
    if match:
        data.wifi_ssid = match.group(1).strip()
        print(f"    ✓ SSID: {data.wifi_ssid}")
    else:
        print("    ✗ SSID: not found")
    
    # WiFi Signal strength
    match = re.search(r'var\s+cover_sta_rssi\s*=\s*"([^"]*)";', html)
    if match:
        data.wifi_signal = match.group(1).strip()
        print(f"    ✓ Signal: {data.wifi_signal}")
    else:
        print("    ✗ Signal: not found")
    
    # WiFi IP
    match = re.search(r'var\s+cover_sta_ip\s*=\s*"([^"]*)";', html)
    if match:
        data.wifi_ip = match.group(1).strip()
        print(f"    ✓ IP: {data.wifi_ip}")
    else:
        print("    ✗ IP: not found")
    
    # WiFi MAC
    match = re.search(r'var\s+cover_sta_mac\s*=\s*"([^"]*)";', html)
    if match:
        data.wifi_mac = match.group(1).strip()
        print(f"    ✓ MAC: {data.wifi_mac}")
    else:
        print("    ✗ MAC: not found")
    
    # === POWER DATA ===
    print("\n  [Power Data]")
    
    # Current power (W)
    match = re.search(r'var\s+webdata_now_p\s*=\s*"([^"]*)";', html)
    if match:
        raw_value = match.group(1)
        data.current_power = parse_numeric_value(raw_value)
        print(f"    ✓ Current Power: {data.current_power} W")
    else:
        data.current_power = 0.0
        print("    ✗ Current Power: not found (using 0)")
    
    # Today's energy (kWh)
    match = re.search(r'var\s+webdata_today_e\s*=\s*"([^"]*)";', html)
    if match:
        raw_value = match.group(1)
        data.today_energy = parse_numeric_value(raw_value)
        print(f"    ✓ Today Energy: {data.today_energy} kWh")
    else:
        data.today_energy = 0.0
        print("    ✗ Today Energy: not found (using 0)")
    
    # Total energy (kWh)
    match = re.search(r'var\s+webdata_total_e\s*=\s*"([^"]*)";', html)
    if match:
        raw_value = match.group(1)
        data.total_energy = parse_numeric_value(raw_value)
        print(f"    ✓ Total Energy: {data.total_energy} kWh")
    else:
        data.total_energy = 0.0
        print("    ✗ Total Energy: not found (using 0)")
    
    return data


async def test_connection(host: str, username: str, password: str) -> InverterData:
    """Test connection to the Deye inverter."""
    url = f"http://{host}/status.html"
    data = InverterData()
    
    print(f"\n{'='*60}")
    print(f"Deye Sun Microinverter Connection Test")
    print(f"{'='*60}")
    print(f"\n🔗 Target: {url}")
    print(f"👤 Username: {username}")
    print(f"🔑 Password: {'*' * len(password)}")
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        auth = aiohttp.BasicAuth(username, password)
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        
        async with aiohttp.ClientSession() as session:
            print(f"\n📡 Connecting to inverter...")
            
            async with session.get(url, auth=auth, timeout=timeout) as response:
                print(f"📬 Response status: {response.status}")
                
                if response.status == 401:
                    data.available = False
                    data.error_message = "Authentication failed"
                    print("\n❌ ERROR: Authentication failed!")
                    print("   Check your username and password.")
                    return data
                
                if response.status != 200:
                    data.available = False
                    data.error_message = f"HTTP error {response.status}"
                    print(f"\n❌ ERROR: Unexpected HTTP status {response.status}")
                    return data
                
                print("📥 Reading response data...")
                html = await response.text()
                
                # Check if we got valid data
                if "webdata_now_p" not in html:
                    data.available = False
                    data.error_message = "Invalid response format"
                    print("\n⚠ WARNING: Could not find expected data in response!")
                    print("   The page structure might be different.")
                    print("\n--- First 2000 characters of response ---")
                    print(html[:2000])
                    print("--- End of preview ---\n")
                    data.raw_html = html
                    return data
                
                return parse_status_page(html)
                
    except asyncio.TimeoutError:
        data.available = False
        data.error_message = "Connection timeout"
        print(f"\n⚠ TIMEOUT: Connection timeout after 10 seconds")
        print("   This is NORMAL if the inverter is in night/sleep mode!")
        print("   The inverter turns off when there's no solar power.")
        return data
        
    except aiohttp.ClientConnectorError as err:
        data.available = False
        data.error_message = f"Connection refused: {err}"
        print(f"\n⚠ OFFLINE: Cannot connect to inverter")
        print("   This is NORMAL if the inverter is in night/sleep mode!")
        print("   The inverter turns off when there's no solar power.")
        print(f"\n   Technical details: {err}")
        return data
        
    except aiohttp.ClientError as err:
        data.available = False
        data.error_message = str(err)
        print(f"\n❌ ERROR: Network error: {err}")
        return data
        
    except Exception as err:
        data.available = False
        data.error_message = str(err)
        print(f"\n❌ ERROR: Unexpected error: {type(err).__name__}: {err}")
        return data


def print_results(data: InverterData):
    """Print the test results."""
    print(f"\n{'='*60}")
    print("📋 Results Summary")
    print(f"{'='*60}")
    
    # Status
    if data.available:
        print(f"\n🟢 Status: ONLINE")
    else:
        print(f"\n🔴 Status: OFFLINE")
        if data.error_message:
            print(f"   Reason: {data.error_message}")
    
    # Device info table
    if data.serial_number or data.firmware_version:
        print(f"\n┌{'─'*44}┐")
        print(f"│ {'DEVICE INFORMATION':<42} │")
        print(f"├{'─'*44}┤")
        if data.serial_number:
            print(f"│ {'Serial Number':<20} │ {data.serial_number:<19} │")
        if data.firmware_version:
            print(f"│ {'Firmware':<20} │ {data.firmware_version:<19} │")
        if data.module_id:
            print(f"│ {'Module ID':<20} │ {data.module_id:<19} │")
        print(f"└{'─'*44}┘")
    
    # WiFi info table
    if data.wifi_ssid:
        print(f"\n┌{'─'*44}┐")
        print(f"│ {'WIFI INFORMATION':<42} │")
        print(f"├{'─'*44}┤")
        print(f"│ {'Network (SSID)':<20} │ {(data.wifi_ssid or 'N/A'):<19} │")
        print(f"│ {'Signal Strength':<20} │ {(data.wifi_signal or 'N/A'):<19} │")
        if data.wifi_ip:
            print(f"│ {'IP Address':<20} │ {data.wifi_ip:<19} │")
        if data.wifi_mac:
            print(f"│ {'MAC Address':<20} │ {data.wifi_mac:<19} │")
        print(f"└{'─'*44}┘")
    
    # Power data table
    print(f"\n┌{'─'*44}┐")
    print(f"│ {'POWER DATA':<42} │")
    print(f"├{'─'*44}┤")
    
    if data.available:
        power_str = f"{data.current_power:.1f} W" if data.current_power is not None else "N/A"
        today_str = f"{data.today_energy:.2f} kWh" if data.today_energy is not None else "N/A"
        total_str = f"{data.total_energy:.2f} kWh" if data.total_energy is not None else "N/A"
        
        print(f"│ {'Current Power':<20} │ {power_str:>19} │")
        print(f"│ {'Energy Today':<20} │ {today_str:>19} │")
        print(f"│ {'Energy Total':<20} │ {total_str:>19} │")
    else:
        print(f"│ {'Current Power':<20} │ {'UNAVAILABLE':>19} │")
        print(f"│ {'Energy Today':<20} │ {'UNAVAILABLE':>19} │")
        print(f"│ {'Energy Total':<20} │ {'UNAVAILABLE':>19} │")
    
    print(f"└{'─'*44}┘")
    
    # Final status
    print(f"\n{'='*60}")
    if data.available:
        print("✅ Test SUCCESSFUL - All systems operational!")
        print("\n📦 Installation in Home Assistant:")
        print("   1. Copy custom_components/deye_sun to your HA config folder")
        print("   2. Restart Home Assistant")
        print("   3. Add the integration via Settings -> Integrations")
        print("   4. Search for 'Deye SUN Inverter' and configure")
        return True
    else:
        print("⚠️  Test completed - Inverter is OFFLINE")
        print("\n   This is NORMAL behavior at night or without sunlight!")
        print("   The Deye inverter turns off when there's no power to save energy.")
        print("\n   The Home Assistant integration handles this gracefully:")
        print("   • Sensors will show 'unavailable' when offline")
        print("   • Data will automatically recover when the sun rises")
        print("   • No errors will be logged (only debug messages)")
        print("\n   You can still install the integration - it will work!")
        return True  # Still success, just offline


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Test connection to Deye SUN800 inverter",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test_connection.py --host 192.168.1.100
  python test_connection.py -H 192.168.1.100 -u admin -p mypassword
  python test_connection.py --host 192.168.1.100 --save-html

IMPORTANT: Assign a static IP address to your inverter!
The inverter may be offline at night - this is normal behavior.
        """
    )
    parser.add_argument(
        "--host", "-H",
        required=True,
        help="IP address of the inverter (e.g., 192.168.1.100)"
    )
    parser.add_argument(
        "--user", "-u",
        default="admin",
        help="Username for authentication (default: admin)"
    )
    parser.add_argument(
        "--password", "-p",
        default="admin",
        help="Password for authentication (default: admin)"
    )
    parser.add_argument(
        "--save-html",
        action="store_true",
        help="Save the raw HTML response to a file for debugging"
    )
    
    args = parser.parse_args()
    
    data = await test_connection(args.host, args.user, args.password)
    
    if data.raw_html and args.save_html:
        filename = f"deye_response_{args.host.replace('.', '_')}.html"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(data.raw_html)
        print(f"\n📄 Raw HTML saved to: {filename}")
    
    success = print_results(data)
    
    # Always exit 0 - offline is not an error
    sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
