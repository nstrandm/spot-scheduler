"""Constants for SpotScheduler."""

DOMAIN = "spot_scheduler"
STORAGE_KEY = f"{DOMAIN}.schedules"
STORAGE_VERSION = 1

# Increment this whenever the card JS changes to force browser cache refresh
CARD_VERSION = "4"

CONF_NORDPOOL_CONFIG_ENTRY = "nordpool_config_entry"
CONF_DEVICES = "devices"
CONF_EXPENSIVE_HOURS_COUNT = "expensive_hours_count"
CONF_AUTO_SELECT_HOURS    = "auto_select_hours"

DEFAULT_EXPENSIVE_HOURS   = 3
DEFAULT_AUTO_SELECT_HOURS = 0   # 0 = disabled

# Price color thresholds (EUR/kWh cents) – 0 means "use relative scaling"
CONF_PRICE_THRESHOLD_LOW = "price_threshold_low"
CONF_PRICE_THRESHOLD_HIGH = "price_threshold_high"
DEFAULT_PRICE_THRESHOLD_LOW = 5.0    # below this = green (cents/kWh)
DEFAULT_PRICE_THRESHOLD_HIGH = 15.0  # above this = red (cents/kWh)

NORDPOOL_DOMAIN = "nordpool"

# Issue registry identifiers
ISSUE_NORDPOOL_MISSING    = "nordpool_integration_missing"
ISSUE_NORDPOOL_UNAVAILABLE = "nordpool_unavailable"

# How often to poll for tomorrow's prices when they haven't arrived yet.
# Core Nord Pool has no tomorrow_valid attribute, so we poll after ~13:00 local.
TOMORROW_POLL_INTERVAL_MINUTES = 15
TOMORROW_POLL_START_HOUR = 13   # don't bother polling before this local hour

# Option: auto-select cheapest hours (global on/off toggle)
CONF_AUTO_SELECT_ENABLED = "auto_select_enabled"
DEFAULT_AUTO_SELECT_ENABLED = True  # on by default; count=0 still disables it

# Option: auto-set expensive hours to OFF when prices arrive
CONF_BLOCK_EXPENSIVE_HOURS = "block_expensive_hours"
DEFAULT_BLOCK_EXPENSIVE = False
