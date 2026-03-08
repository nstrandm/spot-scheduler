# Spot Scheduler

> Run your appliances when electricity is cheapest — Nord Pool-powered scheduling that automatically picks the cheapest hours and executes them on time.

![Spot Scheduler card](images/card-screenshot.png)

Spot Scheduler adds a Lovelace card that shows hourly electricity prices as a bar chart and lets you click each cell to schedule a device **on**, **off**, or leave it **unset** (don't touch) for that hour. Schedules are stored persistently and executed automatically at the start of each hour.

**Requires:** Home Assistant 2025.1+ with the built-in [Nord Pool integration](https://www.home-assistant.io/integrations/nordpool/).

---

## Features

- 📊 **Hourly price chart** — 15-minute MTU slots are averaged into hourly prices
- 🔴 **Expensive hours highlighted** — configurable count, default 3 most expensive per day
- 📅 **Day min / max price** shown in the card header
- ✅ **Three-state per-device toggle** — On / Off / Unset (don't touch) for every device and hour
- 🤖 **Auto-select cheapest hours** — automatically marks the N cheapest hours as ON when prices arrive
- 🚫 **Block expensive hours** — automatically marks the N most expensive hours as OFF
- 📆 **Multi-day view** — navigate up to 6 days ahead to pre-schedule devices; also 1 day back (yesterday)
- 💾 **Persistent schedules** — saved to HA storage, survive restarts, included in HA backups
- ⏰ **Automatic execution** — devices are turned on/off at the start of each scheduled hour
- 🌐 **Multilingual UI** — follows your HA profile language setting (English / Finnish)
- 🔔 **HA Repairs integration** — actionable alerts if Nord Pool becomes unavailable
- 🕛 **Midnight cleanup** — old schedule data pruned automatically

---

## How price fetching works

Spot Scheduler uses the Nord Pool integration's `nordpool.get_prices_for_date` service action:

| Event | Action |
|---|---|
| HA startup | Fetch today's prices |
| Every 15 min after 13:00 local time | Poll for tomorrow's prices (stops once fetched) |
| Any Nord Pool sensor state change | Opportunistically try fetching tomorrow's prices |
| Midnight | Fetch fresh prices for the new day, prune old data |

Tomorrow's prices in the Nordics are typically published between **13:00–15:00 CET** (14:00–16:00 EET in Finland). SpotScheduler polls for them every 15 minutes starting at 13:00 local time and also reacts to any Nord Pool sensor update. Once tomorrow's prices are fetched, polling stops until the next day.

Auto-select and block-expensive logic runs **only when prices first arrive** for a date — not on HA restarts or reloads — to avoid overwriting manual schedules or changing device state mid-hour.

---

## Requirements

| Requirement | Version |
|---|---|
| Home Assistant | 2025.1.0+ |
| Nord Pool (built-in) | included in HA 2025.1+ |
| HACS | 1.0+ (for HACS install) |

> **Note:** This integration uses the **built-in** Nord Pool integration, not the old HACS custom component. Make sure Nord Pool is set up under *Settings → Devices & Services* before installing SpotScheduler.

---

## Installation

### Via HACS (recommended)

1. Open HACS → **Integrations** → ⋮ → **Custom repositories**
2. Add `https://github.com/nstrandm/spot-scheduler` → category **Integration**
3. Find **Spot Scheduler** and click **Download**
4. **Restart Home Assistant**
5. Go to **Settings → Devices & Services → + Add integration → SpotScheduler**

The Lovelace card JS resource is registered automatically when the integration starts — no manual resource registration needed.

### Manual installation

1. Copy the `custom_components/spot_scheduler/` folder to your HA `config/custom_components/` directory
2. **Restart Home Assistant**
3. Go to **Settings → Devices & Services → + Add integration → SpotScheduler**

The card resource is registered automatically on first startup. If auto-registration fails (e.g. YAML-mode dashboards), add the resource manually:

**Settings → Dashboards → ⋮ → Resources → Add resource:**

| Field | Value |
|---|---|
| URL | `/api/spot_scheduler/static/spot-scheduler-card.js` |
| Type | JavaScript module |

---

## Setup

### Settings

![Config flow](images/config-flow.png)

Pick devices from HA's entity list. Supported domains: `switch`, `light`, `climate`, `input_boolean`.

Choose the Nord Pool integration entry, give the integration a name, and set how many of the most expensive hours to highlight in red.

### Configuration entities

After setup, SpotScheduler adds the following entities under **Settings → Devices & Services → Spot Scheduler** (Configuration section):

| Entity | Description |
|---|---|
| **Cheapest hours** | How many cheapest hours per day to auto-select as ON (0 = disabled) |
| **Cheapest hours auto-select** | Switch to enable/disable auto-select globally |
| **Expensive hours** | How many most-expensive hours to highlight in red |
| **Expensive hours turn off** | Switch to automatically mark expensive hours as OFF |
| **Max price limit** | Prices above this (¢/kWh) are coloured red in the bar chart |
| **Min price limit** | Prices below this (¢/kWh) are coloured green in the bar chart |

### Changing settings later

Go to **Settings → Devices & Services → Spot Scheduler → Configure** to modify devices and the expensive hours threshold at any time. Changes take effect immediately after saving.

---

## Adding the card to your dashboard

1. Open your dashboard → **Edit** (pencil icon) → **+ Add card**
2. Search for **Spot Scheduler** in the card picker, or choose **Manual** and paste:

**Minimal — uses all settings from the integration:**

```yaml
type: custom:spot-scheduler-card
```

**Full example with overrides:**

```yaml
type: custom:spot-scheduler-card
devices:
  - switch.washing_machine
  - switch.ev_charger
  - climate.floor_heating
device_names:
  switch.washing_machine: "Washing machine"
  switch.ev_charger: "EV charger"
expensive_hours: 3
show_price_labels: true
```

### Card options

| Option | Type | Default | Description |
|---|---|---|---|
| `devices` | list | auto-detected | Entity IDs to schedule. If omitted, the integration's configured device list is used. |
| `device_names` | map | `{}` | Custom display names per entity ID, e.g. `switch.foo: "My device"`. Falls back to HA friendly name. |
| `expensive_hours` | int | auto-detected | Most expensive hours to highlight in red. If omitted, uses the value from integration settings. |
| `title` | string | `"SpotScheduler"` | Card title (overrides translated default) |
| `show_price_labels` | bool | `false` | Show the cent price on top of each price bar |
| `label_width` | int | `120` | Width in px of the device name column |
| `status_entity` | string | auto-detected | Override the sensor used to read prices/schedules |

> **Note:** `devices` and `expensive_hours` are read from the integration automatically if not set in the card YAML. Values explicitly set in the card YAML always take priority over integration settings. The card reads schedule data from the integration — it does not control devices on its own.

### Recommended dashboard layout

Use the **Masonry** layout (the default). On mobile, Masonry automatically uses a single full-width column, giving the card maximum width for the 24-column schedule grid.

---

## Daily use

1. **Prices for tomorrow** appear automatically after Nord Pool publishes them (typically ~14:00–16:00 EET for Finland)
2. Open your dashboard — the bar chart shows hourly average prices
3. The **most expensive hours** are highlighted with a red border
4. **Click a cell** to cycle through three states:
   - **✔ blue** — device will turn **on** at the start of that hour
   - **✕ grey** — device will turn **off** at the start of that hour
   - **faint** — **unset** / don't touch — SpotScheduler leaves the device in whatever state it's in
5. Use **◀ ▶** to navigate between days (1 day back, up to 6 days forward)
6. Future days (beyond tomorrow) show the schedule grid without price bars — you can still pre-set manual schedules

---

## Sensors

| Entity | Description |
|---|---|
| `sensor.spotscheduler_schedule_status` | Number of ON-hours scheduled today; attributes include full price and schedule data used by the card |

The sensor updates automatically when prices arrive or schedules change. Prices and schedules for all available dates are exposed as sensor attributes and consumed by the card.

---

## Services

### `spot_scheduler.set_device_schedule`

Set a device schedule slot (also called by the card automatically when you click a cell).

```yaml
service: spot_scheduler.set_device_schedule
data:
  date: "2026-03-05"          # ISO date, defaults to today
  hour: 2                     # 0–23
  device_id: switch.ev_charger
  enabled: true               # true = on, false = off, omit = unset (clear)
```

### `spot_scheduler.refresh_prices`

Force a price refresh for a specific date. Fetches for all configured SpotScheduler instances.

```yaml
service: spot_scheduler.refresh_prices
data:
  date: "2026-03-05"          # defaults to today
```

### `spot_scheduler.apply_schedules_now`

Immediately apply the current hour's schedule to all managed devices — exactly like the automatic trigger at `:00:05`, but callable at any time. Useful during development and testing.

```yaml
service: spot_scheduler.apply_schedules_now
data: {}                      # no parameters required
# Optional: limit to one SpotScheduler instance
# data:
#   entry_id: "abc123def456"
```

All three services are visible with full field descriptions in **Developer Tools → Services**.

---

## Troubleshooting

### Card shows "Waiting for today's prices from Nord Pool"

- Verify Nord Pool is working: check **Developer Tools → States** for `sensor.nordpool_*` entities
- Try **Developer Tools → Services → `spot_scheduler.refresh_prices`**
- Check the HA log for errors containing `spot_scheduler`

### Card doesn't appear in the card picker

- Verify the integration is running: **Settings → Devices & Services → SpotScheduler**
- Clear browser cache (`Ctrl+Shift+R`)
- On the HA mobile app: **Settings → Companion App → Reset frontend cache**
- If using YAML-mode dashboards, add the resource manually (see Installation section)

### "Nord Pool integration removed" Repairs alert

The linked Nord Pool config entry was deleted. Re-add Nord Pool under **Settings → Devices & Services**, then reload SpotScheduler.

### Schedule toggles don't persist

Check that the device entity IDs in your card config match those in the integration setup. If you changed devices via **Configure**, you may need to update the card YAML as well.

### Devices don't turn on/off at the scheduled time

- SpotScheduler sends `homeassistant.turn_on` / `turn_off` at `HH:00:05` each hour
- Verify the target device responds to these service calls in Developer Tools
- Check the HA log for `Schedule: ON` / `Schedule: OFF` messages

---

## Languages

The card language follows the **HA user profile** setting (`hass.locale.language`).

| Language | Code | Status |
|---|---|---|
| English | `en` | ✅ |
| Finnish | `fi` | ✅ |

To add a new language, add an entry to the `TRANSLATIONS` object in `www/spot-scheduler-card.js` and a new file under `custom_components/spot_scheduler/translations/`.
