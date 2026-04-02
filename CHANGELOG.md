# Changelog

## [0.2.6] — 2026-04-02

### Changed
- Fixed HACS validation actions

## [0.2.4] — 2026-04-02

### Changed
- Removed legacy per-day sensor attributes (`prices_tomorrow`, `schedules_tomorrow`, etc.) — all data now via `prices_all` / `schedules_all`
- `prices_all` filters out dates with < 20 hours (CET timezone spillover)
- Simplified frontend data sync — removed fallback paths for legacy attributes

## [0.2.3] — 2026-03-31

### Added
- 6-day forward navigation — pre-schedule devices before prices are available
- `prices_all` and `schedules_all` sensor attributes for multi-day data
- "Prices not yet available" message for future days without prices (en + fi)

### Changed
- Auto-select now fills only unscheduled slots, preserving manual ON/OFF/skip choices
- Already-ON hours count toward the cheapest-hours target (no over-selection)
- CET timezone spillover hours (< 20h) no longer shown as a price chart

## [0.2.2] — 2026-03-30

### Added
- Default state setting: On / Off / Don't touch for unscheduled hours
- "Don't touch" (skip) as explicit schedule state — overrides default state
- 4-state toggle cycle when default state is On or Off

## [0.2.1] — 2026-03-29

### Fixed
- BOM encoding issue in frontend JS

## [0.2.0] — 2026-03-28

### Fixed
- Price parsing and display fixes

## [0.1.9] — 2026-03-27

### Changed
- UI modifications and layout option added to card editor

## [0.1.8] — 2026-03-26

### Fixed
- Automatic frontend JS resource registration (no more manual resource setup)
- Card JS moved from `www/` to `custom_components/spot_scheduler/frontend/`

## [0.1.7] — 2026-03-25

### Added
- Vertical layout — hours as rows, devices as columns

## [0.1.6] — 2026-03-24

### Added
- Mobile-responsive split layout (AM / PM rows)

## [0.1.5] — 2026-03-23

### Added
- Initial stable release
- Hourly price chart with Nord Pool integration
- Per-device schedule toggle (On / Off / Unset)
- Auto-select cheapest hours
- Block expensive hours
- Persistent schedules (HA storage)
- Automatic execution at each hour
- Multilingual UI (English / Finnish)
- HA Repairs integration
- Midnight cleanup of old data
