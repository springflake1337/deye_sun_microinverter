"""Constants for the Deye Sun Microinverter integration."""

DOMAIN = "deye_sun_microinverter"

# Configuration
CONF_HOST = "host"
CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_SCAN_INTERVAL = "scan_interval"

# Defaults
DEFAULT_USERNAME = "admin"
DEFAULT_PASSWORD = "admin"
DEFAULT_SCAN_INTERVAL = 30  # seconds

# Update intervals for different data types
WIFI_UPDATE_INTERVAL = 900  # 15 minutes in seconds
DEVICE_INFO_UPDATE_INTERVAL = 86400  # 24 hours in seconds
