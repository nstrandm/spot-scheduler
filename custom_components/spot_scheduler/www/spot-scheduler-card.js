// Spot Scheduler – Lovelace Custom Card
// Language is taken from hass.locale.language (set in HA user profile)
// Supported: en, fi  |  Falls back to English for unknown languages.

const TRANSLATIONS = {
  en: {
    title: "Spot Scheduler",
    subtitle: "Schedule cheapest hours automatically · Nord Pool spot prices",
    prices_note: "Prices fetched automatically when available",
    prices_pending: "⏳ Waiting for today's prices from Nord Pool",
    on: "On",
    off: "Off",
    unset: "–",
    legend_on: "On",
    legend_off: "Off",
    legend_unset: "Don't touch",
    legend_expensive: "Expensive (top {n})",
    legend_current: "Current hour",
    stat_min: "Min",
    stat_max: "Max",
    price_row_label: "Avg price (€/kWh) · 15 min slots → hourly average",
    no_devices: "No devices configured.",
    save_hint: "✓ Changes saved automatically to Home Assistant",
    // Editor labels
    editor_title:             "Title (empty = default)",
    editor_expensive_hours:   "Expensive hours highlight (0 = none)",
    editor_show_price_labels: "Show cent price on each bar",
    editor_label_width:       "Device name column width (px)",
    editor_status_entity:     "Status sensor (empty = auto-detect)",
    editor_device_names:      "Device names on card",
    editor_no_devices:        "No devices detected yet. Save the card first.",
    editor_device_placeholder: "Friendly name…",
  },
  fi: {
    title: "Spot Scheduler",
    subtitle: "Halvimmat tunnit automaattisesti · Nord Pool pörssisähkö",
    prices_note: "Hinnat haetaan automaattisesti kun saatavilla",
    prices_pending: "⏳ Odotetaan päivän hintoja Nord Poolilta",
    on: "Päällä",
    off: "Pois",
    unset: "–",
    legend_on: "Päällä",
    legend_off: "Pois",
    legend_unset: "Älä koske",
    legend_expensive: "Kallis ({n} kalleinta)",
    legend_current: "Nykyinen tunti",
    stat_min: "Min",
    stat_max: "Max",
    price_row_label: "Tunnin keskihinta (€/kWh) · 15 min arvoista laskettu",
    no_devices: "Ei laitteita konfiguroitu.",
    save_hint: "✓ Muutokset tallentuvat automaattisesti Home Assistantiin",
    // Editor labels
    editor_title:             "Otsikko (tyhjä = oletusarvo)",
    editor_expensive_hours:   "Kalliiden tuntien korostus (0 = ei mitään)",
    editor_show_price_labels: "Näytä senttihinta jokaisessa palkissa",
    editor_label_width:       "Laitenimen sarakeleveys (px)",
    editor_status_entity:     "Status-sensori (tyhjä = automaattinen)",
    editor_device_names:      "Laitteiden nimet kortilla",
    editor_no_devices:        "Laitteita ei havaittu. Tallenna kortti ensin.",
    editor_device_placeholder: "Kutsumanimi…",
  },
};

function _t(lang, key, vars = {}) {
  const base = TRANSLATIONS[lang] || TRANSLATIONS.en;
  let str = base[key] ?? TRANSLATIONS.en[key] ?? key;
  for (const [k, v] of Object.entries(vars)) str = str.replace(`{${k}}`, v);
  return str;
}

// ── CSS ──────────────────────────────────────────────────────────────────────
const STYLES = `
  :host { display: block; font-family: var(--primary-font-family, 'Segoe UI', system-ui, sans-serif); }
  .card { background: var(--ha-card-background, var(--card-background-color));
    border-radius: var(--ha-card-border-radius, 12px);
    padding: 20px; color: var(--primary-text-color);
    box-shadow: var(--ha-card-box-shadow, var(--material-shadow-elevation-2dp));
    overflow: hidden; }
  .header { display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:18px; }
  .title { font-size:20px; font-weight:700; color:var(--primary-text-color); }
  .subtitle { font-size:13px; color:var(--secondary-text-color); margin-top:3px; }
  .stats { display:flex; gap:9px; }
  .stat-box { background:var(--secondary-background-color); border-radius:9px;
    padding:8px 14px; text-align:center; min-width:80px; }
  .stat-label { font-size:11px; color:var(--secondary-text-color);
    text-transform:uppercase; letter-spacing:.8px; }
  .stat-value { font-size:15px; font-weight:700; margin-top:2px; }
  .date-nav { display:flex; align-items:center; gap:9px; margin-bottom:14px; }
  .date-btn { background:var(--secondary-background-color); border:none;
    color:var(--secondary-text-color); width:32px; height:32px;
    border-radius:6px; cursor:pointer; font-size:15px;
    display:flex; align-items:center; justify-content:center; }
  .date-btn:hover { filter:brightness(1.15); }
  .date-btn:disabled { opacity:0.3; cursor:default; filter:none; }
  .date-lbl { font-size:15px; font-weight:600; color:var(--primary-text-color); }
  .prices-note { font-size:11px; color:var(--disabled-text-color); margin-left:auto; }
  .legend { display:flex; gap:13px; flex-wrap:wrap; margin-bottom:14px; }
  .leg-item { display:flex; align-items:center; gap:6px;
    font-size:13px; color:var(--secondary-text-color); }
  .leg-dot { width:11px; height:11px; border-radius:50%; flex-shrink:0; }
  .price-section { margin-bottom:14px; }
  .price-lbl { font-size:12px; color:var(--disabled-text-color); margin-bottom:5px; }
  .bars { display:flex; align-items:flex-end; gap:2px; height:100px; }
  .bar-col { flex:1; min-width:28px; display:flex; flex-direction:column; align-items:center; justify-content:flex-end; height:100%; }
  .bar { width:100%; border-radius:2px 2px 0 0; min-height:2px; }
  .bar.exp { box-shadow:0 0 5px color-mix(in srgb, var(--error-color, #f87171) 65%, transparent); }
  .divider { height:1px; background:var(--divider-color); margin:13px 0; }
  .scroll-wrap { overflow-x:auto; overflow-y:hidden; }
  .grid-scroll { overflow-x:visible; overflow-y:hidden; }
  .gh { text-align:center; font-size:12px; color:var(--disabled-text-color);
    font-weight:700; padding:2px 0; }
  .gh.cur { color:var(--primary-color); }
  .dev-lbl { font-size:13px; font-weight:600; color:var(--primary-text-color);
    display:flex; align-items:center; padding-right:5px;
    white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
  .cell { aspect-ratio:1; border-radius:4px; border:2px solid transparent;
    display:flex; align-items:center; justify-content:center; margin: 2px;
    font-size:13px; font-weight:700; cursor:pointer; min-height:24px;
    transition:transform .1s; }
  .cell:hover { transform:scale(1.1); z-index:5; position:relative; }
  .cell.on { background:var(--primary-color); border-color:var(--primary-color);
    color:var(--text-primary-color, #fff);
    box-shadow:0 0 6px color-mix(in srgb, var(--primary-color) 45%, transparent); }
  .cell.off { background:var(--secondary-background-color);
    border-color:var(--divider-color); color:var(--disabled-text-color); }
  .cell.unset { background:transparent; border-color:var(--divider-color);
    color:var(--disabled-text-color); opacity:0.35; }
  .cell.exp-cell { border-color:var(--error-color, #f87171) !important; }
  .cell.cur-cell { box-shadow:0 0 0 2.5px var(--warning-color, #ff9800); }
  .no-prices { text-align:center; padding:20px; color:var(--disabled-text-color);
    font-size:13px; }
  .save-hint { text-align:right; font-size:10px; color:var(--disabled-text-color);
    margin-top:11px; font-style:italic; }
  .bar-price { font-size:9px; color:var(--secondary-text-color); text-align:center;
    line-height:1.2; min-height:12px; }
`;

// ── Helpers ───────────────────────────────────────────────────────────────────

function _todayISO() {
  const d = new Date();
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

function _el(tag, cls, text) {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text !== undefined) e.textContent = text;
  return e;
}

// ── Card class ────────────────────────────────────────────────────────────────
class SpotSchedulerCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._config = {};
    this._hass = null;
    this._schedules = {};
    this._prices = {};
    this._minPrice = null;
    this._maxPrice = null;
    this._selectedDate = _todayISO();
    this._lang = "en";
    this._statusEntity = null;

    // Persistent DOM element references (populated once in _buildDOM)
    this._dom = null;
  }

  // ── HA lifecycle ────────────────────────────────────────────────────────────
  setConfig(config) {
    this._config = {
      title: null,
      devices: [],          // populated from sensor if not in config
      device_names: {},      // optional: { "light.foo": "Custom Name" }
      expensive_hours: 3,    // populated from sensor if not in config
      label_width: 120,
      show_price_labels: false,
      ...config,
      // Track whether values came from YAML so sensor doesn't override them
      _devicesFromYaml: !!(config.devices?.length),
      _expensiveFromYaml: config.expensive_hours !== undefined,
    };
    this._dom = null;
    this._update();
  }

  set hass(hass) {
    const prev = this._hass;
    this._hass = hass;

    const raw = hass?.locale?.language ?? "en";
    this._lang = TRANSLATIONS[raw] ? raw : "en";

    if (!this._statusEntity) {
      this._statusEntity = this._config?.status_entity || this._findStatusEntity();
      if (!this._statusEntity) return;
      const state = hass?.states[this._statusEntity];
      if (state) { this._syncFromSensor(state); this._update(); }
      return;
    }

    const prevState = prev?.states[this._statusEntity];
    const newState  = hass?.states[this._statusEntity];
    if (newState && newState !== prevState) {
      this._syncFromSensor(newState);
      this._update();
    }
  }

  // ── Load prices + schedules from the status sensor ─────────────────────────
  _syncFromSensor(state) {
    const attrs = state?.attributes ?? {};
    const today    = _todayISO();
    const tomorrow = (() => {
      const d = new Date(); d.setDate(d.getDate() + 1);
      const y = d.getFullYear();
      const m = String(d.getMonth() + 1).padStart(2, "0");
      const day = String(d.getDate()).padStart(2, "0");
      return `${y}-${m}-${day}`;
    })();
    const yesterday = (() => {
      const d = new Date(); d.setDate(d.getDate() - 1);
      const y = d.getFullYear();
      const m = String(d.getMonth() + 1).padStart(2, "0");
      const day = String(d.getDate()).padStart(2, "0");
      return `${y}-${m}-${day}`;
    })();

    const todayPrices     = attrs.prices ?? {};
    const tomorrowPrices  = attrs.prices_tomorrow ?? {};
    const yesterdayPrices = attrs.prices_yesterday ?? {};

    if (Object.keys(todayPrices).length) {
      this._prices[today] = {};
      for (const [h, v] of Object.entries(todayPrices))
        this._prices[today][parseInt(h)] = v;
    }
    if (Object.keys(tomorrowPrices).length) {
      this._prices[tomorrow] = {};
      for (const [h, v] of Object.entries(tomorrowPrices))
        this._prices[tomorrow][parseInt(h)] = v;
    }
    if (Object.keys(yesterdayPrices).length) {
      this._prices[yesterday] = {};
      for (const [h, v] of Object.entries(yesterdayPrices))
        this._prices[yesterday][parseInt(h)] = v;
    }
    if (attrs.schedules !== undefined) {
      this._schedules[today] = attrs.schedules ?? {};
    }
    if (attrs.schedules_tomorrow !== undefined) {
      this._schedules[tomorrow] = attrs.schedules_tomorrow ?? {};
    }
    if (attrs.schedules_yesterday !== undefined) {
      this._schedules[yesterday] = attrs.schedules_yesterday ?? {};
    }
    if (attrs.min_price != null) this._minPrice = attrs.min_price;
    if (attrs.max_price != null) this._maxPrice = attrs.max_price;

    // Read integration settings from sensor (unless overridden in card YAML)
    if (attrs.expensive_hours_count != null && !this._config._expensiveFromYaml) {
      this._config.expensive_hours = attrs.expensive_hours_count;
    }
    if (attrs.devices?.length && !this._config._devicesFromYaml) {
      const oldDevices = JSON.stringify(this._config.devices);
      this._config.devices = attrs.devices;
      // Rebuild DOM if device list changed
      if (JSON.stringify(this._config.devices) !== oldDevices) {
        this._dom = null;
      }
    }
    // Price color thresholds (cents/kWh)
    if (attrs.price_threshold_low != null) this._config._thresholdLow = attrs.price_threshold_low;
    if (attrs.price_threshold_high != null) this._config._thresholdHigh = attrs.price_threshold_high;
  }

  _findStatusEntity() {
    if (!this._hass) return null;
    return Object.keys(this._hass.states).find(
      id => id.startsWith("sensor.") &&
            id.includes("schedule_status") &&
            (id.includes("spot_scheduler") || id.includes("spotscheduler"))
    ) ?? null;
  }

  // ── Helpers ─────────────────────────────────────────────────────────────────
  _tr(key, vars = {}) { return _t(this._lang, key, vars); }

  _deviceName(devId) {
    // 1. Custom name from card YAML
    const custom = this._config.device_names?.[devId];
    if (custom) return custom;
    // 2. HA friendly_name
    const state = this._hass?.states?.[devId];
    if (state?.attributes?.friendly_name) return state.attributes.friendly_name;
    // 3. Fallback: parse from entity ID
    return devId.split(".").pop().replace(/_/g, " ");
  }

  _expensiveHours() {
    const today = _todayISO();
    const prices = this._prices[this._selectedDate] ?? {};
    const entries = Object.entries(prices);
    if (!entries.length) return new Set();
    const n = this._config.expensive_hours ?? 3;
    return new Set(
      [...entries].sort((a, b) => b[1] - a[1]).slice(0, n).map(([h]) => parseInt(h))
    );
  }

  _isScheduled(deviceId, hour) {
    return this._schedules?.[this._selectedDate]?.[deviceId]?.[String(hour)] ?? null;
  }

  _toggleSchedule(deviceId, hour) {
    const cur  = this._isScheduled(deviceId, hour);
    // Three-state cycle: null → true → false → null
    const next = cur === null ? true : cur === true ? false : null;

    if (!this._schedules[this._selectedDate]) this._schedules[this._selectedDate] = {};
    if (!this._schedules[this._selectedDate][deviceId]) this._schedules[this._selectedDate][deviceId] = {};
    if (next === null) {
      delete this._schedules[this._selectedDate][deviceId][String(hour)];
    } else {
      this._schedules[this._selectedDate][deviceId][String(hour)] = next;
    }
    this._update();

    if (!this._hass) return;

    // Omit 'enabled' when unsetting (null) — service treats absent as "unset"
    const svcData = { date: this._selectedDate, hour, device_id: deviceId };
    if (next !== null) svcData.enabled = next;

    this._hass.callService("spot_scheduler", "set_device_schedule", svcData)
      .catch(() => {
        // Revert on error
        if (cur === null) {
          delete this._schedules[this._selectedDate][deviceId][String(hour)];
        } else {
          this._schedules[this._selectedDate][deviceId][String(hour)] = cur;
        }
        this._update();
      });
  }

  _priceColor(price) {
    // Price is in EUR/kWh, thresholds are in cents/kWh
    const priceCents = price * 100;
    const low = this._config._thresholdLow ?? 5;
    const high = this._config._thresholdHigh ?? 15;

    if (high <= low) return "#a0c4ff";

    // Clamp ratio: 0 = at or below low threshold, 1 = at or above high threshold
    const r = Math.max(0, Math.min(1, (priceCents - low) / (high - low)));

    // Green → Yellow → Red
    if (r < 0.5) {
      const t = r / 0.5;
      return `rgb(${Math.round(50 + 200 * t)},${Math.round(200 + 55 * (1 - t))},50)`;
    }
    const t = (r - 0.5) / 0.5;
    return `rgb(${Math.round(230 + 25 * t)},${Math.round(200 - 170 * t)},50)`;
  }

  _fmtPrice(p) {
    if (p == null) return "–";
    return (p * 100).toFixed(2) + " c/kWh";
  }

  _canGoPrev() {
    const today = new Date(_todayISO() + "T12:00:00");
    const minDate = new Date(today); minDate.setDate(minDate.getDate() - 1);
    return new Date(this._selectedDate + "T12:00:00") > minDate;
  }

  _canGoNext() {
    const today = new Date(_todayISO() + "T12:00:00");
    const maxDate = new Date(today); maxDate.setDate(maxDate.getDate() + 1);
    return new Date(this._selectedDate + "T12:00:00") < maxDate;
  }

  // ── Build persistent DOM (called once, or when config changes) ─────────────
  _buildDOM() {
    const root = this.shadowRoot;
    root.innerHTML = "";

    const style = document.createElement("style");
    style.textContent = STYLES;
    root.appendChild(style);

    const card = _el("div", "card");
    root.appendChild(card);

    // ── Header ───────────────────────────────────────────────────────────────
    const header = _el("div", "header");
    const headerLeft = _el("div");
    const titleEl = _el("div", "title");
    const subtitleEl = _el("div", "subtitle");
    headerLeft.appendChild(titleEl);
    headerLeft.appendChild(subtitleEl);
    header.appendChild(headerLeft);

    const statsEl = _el("div", "stats");
    const minBox = _el("div", "stat-box");
    const minLabel = _el("div", "stat-label");
    const minValue = _el("div", "stat-value min");
    minBox.appendChild(minLabel); minBox.appendChild(minValue);
    const maxBox = _el("div", "stat-box");
    const maxLabel = _el("div", "stat-label");
    const maxValue = _el("div", "stat-value max");
    maxBox.appendChild(maxLabel); maxBox.appendChild(maxValue);
    statsEl.appendChild(minBox); statsEl.appendChild(maxBox);
    header.appendChild(statsEl);
    card.appendChild(header);

    // ── Date navigation ──────────────────────────────────────────────────────
    const dateNav = _el("div", "date-nav");
    const prevBtn = _el("button", "date-btn", "◀");
    prevBtn.addEventListener("click", () => {
      if (!this._canGoPrev()) return;
      const d = new Date(this._selectedDate + "T12:00:00");
      d.setDate(d.getDate() - 1);
      this._selectedDate = d.toISOString().split("T")[0];
      this._update();
    });
    const dateLbl = _el("span", "date-lbl");
    const nextBtn = _el("button", "date-btn", "▶");
    nextBtn.addEventListener("click", () => {
      if (!this._canGoNext()) return;
      const d = new Date(this._selectedDate + "T12:00:00");
      d.setDate(d.getDate() + 1);
      this._selectedDate = d.toISOString().split("T")[0];
      this._update();
    });
    const pricesNote = _el("span", "prices-note");
    dateNav.append(prevBtn, dateLbl, nextBtn, pricesNote);
    card.appendChild(dateNav);

    // ── Legend ────────────────────────────────────────────────────────────────
    const legend = _el("div", "legend");
    const legDefs = [
      { style: "background:var(--primary-color);border:1.5px solid var(--primary-color)", key: "legend_on" },
      { style: "background:var(--secondary-background-color);border:1.5px solid var(--divider-color)", key: "legend_off" },
      { style: "background:transparent;border:1.5px solid var(--divider-color);opacity:0.4", key: "legend_unset" },
      { style: "background:var(--ha-card-background,var(--card-background-color));border:1.5px solid var(--error-color,#f87171)", key: "legend_expensive" },
      { style: "border:2.5px solid var(--warning-color, #ff9800);background:transparent", key: "legend_current" },
    ];
    const legendSpans = [];
    for (const item of legDefs) {
      const li = _el("div", "leg-item");
      const dot = _el("div", "leg-dot"); dot.style.cssText = item.style;
      const span = _el("span");
      li.append(dot, span);
      legend.appendChild(li);
      legendSpans.push({ span, key: item.key });
    }
    card.appendChild(legend);

    // ── Shared layout constants ─────────────────────────────────────────────
    const devices = this._config.devices ?? [];
    const labelW = this._config.label_width ?? 120;
    const gridCols = `${labelW}px repeat(24, minmax(28px, 1fr))`;

    // ── Price bars ────────────────────────────────────────────────────────────
    const priceSection = _el("div", "price-section");
    const priceLbl = _el("div", "price-lbl");
    const barsContainer = _el("div", "bars");
    // Add empty spacer to align with device label column
    const barSpacer = _el("div");
    barSpacer.style.cssText = `width:${labelW}px;flex-shrink:0`;
    barsContainer.insertBefore(barSpacer, barsContainer.firstChild);
    priceSection.append(priceLbl, barsContainer);

    const barEls = [];
    for (let h = 0; h < 24; h++) {
      const col = _el("div", "bar-col");
      const barPrice = _el("div", "bar-price");
      const bar = _el("div", "bar");
      col.append(barPrice, bar);
      barsContainer.appendChild(col);
      barEls.push({ col, bar, barPrice });
    }

    const noPricesMsg = _el("div", "no-prices");

    // ── Schedule grid ────────────────────────────────────────────────────────
    const gridScroll = _el("div", "grid-scroll");

    // Hour header row – always visible even when prices are unavailable (TODO 2)
    const hourHeaderRow = _el("div");
    hourHeaderRow.style.cssText = `display:grid;grid-template-columns:${gridCols};gap:2px;margin:2px 6px;align-items:center`;
    hourHeaderRow.appendChild(_el("div")); // empty label column
    const hourHeaderCells = [];
    for (let h = 0; h < 24; h++) {
      const cell = _el("div", "gh", String(h));
      hourHeaderRow.appendChild(cell);
      hourHeaderCells.push(cell);
    }
    gridScroll.appendChild(hourHeaderRow);

    // Device rows with persistent cells – event listeners bound once here
    const deviceRows = [];
    for (const devId of devices) {
      const name = this._deviceName(devId);
      const row = _el("div");
      row.style.cssText = `display:grid;grid-template-columns:${gridCols};gap:2px;margin:6px;align-items:center`;
      const lbl = _el("div", "dev-lbl", name); lbl.title = devId;
      row.appendChild(lbl);

      const cells = [];
      for (let h = 0; h < 24; h++) {
        const cell = _el("div", "cell");
        cell.addEventListener("click", () => this._toggleSchedule(devId, h));
        row.appendChild(cell);
        cells.push({ el: cell, devId, hour: h });
      }
      gridScroll.appendChild(row);
      deviceRows.push({ devId, lbl, cells });
    }

    const noDevicesMsg = _el("div", "no-prices");
    gridScroll.appendChild(noDevicesMsg);

    // Shared horizontal scroll container: price bars + schedule grid scroll together (TODO 5)
    const scrollWrap = _el("div", "scroll-wrap");
    scrollWrap.append(priceSection, noPricesMsg, gridScroll);
    card.appendChild(scrollWrap);

    // ── Footer ───────────────────────────────────────────────────────────────
    const saveHint = _el("div", "save-hint");
    card.appendChild(saveHint);

    // Store all mutable references
    this._dom = {
      titleEl, subtitleEl, statsEl, minLabel, minValue, maxLabel, maxValue,
      prevBtn, nextBtn, dateLbl, pricesNote,
      legendSpans,
      priceSection, noPricesMsg, priceLbl, barEls,
      hourHeaderCells,
      deviceRows, noDevicesMsg, saveHint,
    };
  }

  // ── Update DOM in place (called on every data change) ───────────────────────
  _update() {
    if (!this.shadowRoot) return;
    if (!this._dom) this._buildDOM();

    const d = this._dom;
    const lang = this._lang;
    const now = new Date();
    const curHour = now.getHours();
    const today = _todayISO();
    const isToday = this._selectedDate === today;
    const expHours = this._expensiveHours();
    const devices = this._config.devices ?? [];

    const dayPrices = this._prices[this._selectedDate]
      ?? (isToday ? this._prices[today] ?? {} : {});
    const pricesLoaded = Object.keys(dayPrices).length > 0;
    // Global max across all loaded days so scale stays consistent when navigating (TODO 3)
    const allLoadedPrices = Object.values(this._prices).flatMap(day => Object.values(day));
    const maxP = allLoadedPrices.length ? Math.max(...allLoadedPrices) : 0;

    // Header text
    d.titleEl.textContent = this._config.title || this._tr("title");
    d.subtitleEl.textContent = this._tr("subtitle");

    // Stats visibility + values – show for selected day
    const dayPriceValues = Object.values(dayPrices);
    if (dayPriceValues.length) {
      d.statsEl.style.display = "";
      const dayMin = Math.min(...dayPriceValues);
      const dayMax = Math.max(...dayPriceValues);
      d.minLabel.textContent = this._tr("stat_min");
      d.minValue.textContent = this._fmtPrice(dayMin);
      d.minValue.style.color = this._priceColor(dayMin);
      d.maxLabel.textContent = this._tr("stat_max");
      d.maxValue.textContent = this._fmtPrice(dayMax);
      d.maxValue.style.color = this._priceColor(dayMax);
    } else {
      d.statsEl.style.display = "none";
    }

    // Date navigation
    const dispDate = new Date(this._selectedDate + "T12:00:00").toLocaleDateString(
      lang === "fi" ? "fi-FI" : "en-GB",
      { weekday: "short", day: "numeric", month: "short" }
    );
    d.dateLbl.textContent = dispDate;
    d.prevBtn.disabled = !this._canGoPrev();
    d.nextBtn.disabled = !this._canGoNext();
    d.pricesNote.textContent = this._tr("prices_note");

    // Legend text
    for (const { span, key } of d.legendSpans) {
      span.textContent = key === "legend_expensive"
        ? this._tr(key, { n: this._config.expensive_hours ?? 3 })
        : this._tr(key);
    }

    // Price bars – update each bar's style/class in place
    if (pricesLoaded) {
      d.priceSection.style.display = "";
      d.noPricesMsg.style.display = "none";
      d.priceLbl.textContent = this._tr("price_row_label");

      const showPriceLabels = !!this._config.show_price_labels;
      for (let h = 0; h < 24; h++) {
        const { col, bar, barPrice } = d.barEls[h];
        const p = dayPrices[h];
        const barH = p != null ? Math.round((Math.abs(p) / (maxP || 1)) * 88) + 3 : 2;
        const color = p != null ? this._priceColor(p) : "var(--secondary-background-color)";
        const isExp = expHours.has(h);

        bar.style.height = barH + "px";
        bar.style.background = color;
        bar.className = isExp ? "bar exp" : "bar";
        col.title = `${h}:00 – ${this._fmtPrice(p)}`;

        // Price label above each bar (TODO 4)
        if (showPriceLabels && p != null) {
          barPrice.textContent = (p * 100).toFixed(1);
          barPrice.style.display = "";
        } else {
          barPrice.style.display = "none";
        }
      }
    } else {
      d.priceSection.style.display = "none";
      d.noPricesMsg.style.display = "";
      d.noPricesMsg.textContent = this._tr("prices_pending");
    }

    // Schedule grid cells – update only changed attributes
    for (const row of d.deviceRows) {
      // Update device label dynamically (friendly_name may load later)
      const name = this._deviceName(row.devId);
      if (row.lbl.textContent !== name) row.lbl.textContent = name;

      for (const { el, devId, hour } of row.cells) {
        const state = this._isScheduled(devId, hour);
        const isExp = expHours.has(hour);
        const isCur = isToday && hour === curHour;

        let cls = "cell";
        let icon = "";
        if (state === true)        { cls += " on";    icon = "✔"; }
        else if (state === false)  { cls += " off";   icon = "✕"; }
        else                       { cls += " unset"; icon = " "; }
        if (isExp) cls += " exp-cell";
        if (isCur) cls += " cur-cell";

        if (el.className !== cls) el.className = cls;
        if (el.textContent !== icon) el.textContent = icon;
        el.title = `${hour}:00 · ${name} · ${this._fmtPrice(dayPrices[hour])}`;
      }
    }

    // Hour header: highlight current hour (TODO 2)
    for (let h = 0; h < 24; h++) {
      d.hourHeaderCells[h].className = (isToday && h === curHour) ? "gh cur" : "gh";
    }

    // No-devices message
    d.noDevicesMsg.style.display = devices.length ? "none" : "";
    d.noDevicesMsg.textContent = this._tr("no_devices");

    // Footer
    d.saveHint.textContent = this._tr("save_hint");
  }

  getCardSize() { return 6; }

  static getConfigElement() {
    return document.createElement("spot-scheduler-card-editor");
  }

  static getStubConfig() {
    return {};
  }
}

// ── Visual editor ──────────────────────────────────────────────────────────────
class SpotSchedulerCardEditor extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._config         = {};
    this._hass           = null;
    this._form           = null;
    this._namesContainer = null;
  }

  setConfig(config) {
    this._config = { ...config };
    if (this._form) this._form.data = this._formData();
    this._renderDeviceNames();
  }

  set hass(hass) {
    // Only rebuild device-name inputs when the device list actually changes,
    // to avoid wiping text fields the user is currently typing in.
    const prevDeviceList = JSON.stringify(this._devices());
    this._hass = hass;
    if (this._form) this._form.hass = hass;
    if (JSON.stringify(this._devices()) !== prevDeviceList) {
      this._renderDeviceNames();
    }
  }

  connectedCallback() {
    if (!this._form) this._build();
  }

  // Return device list from config or from status sensor attributes
  _devices() {
    if (this._config.devices?.length) return this._config.devices;
    if (!this._hass) return [];
    const sensorId = this._config.status_entity ||
      Object.keys(this._hass.states).find(id =>
        id.startsWith("sensor.") && id.includes("schedule_status") &&
        (id.includes("spot_scheduler") || id.includes("spotscheduler"))
      );
    return this._hass.states?.[sensorId]?.attributes?.devices ?? [];
  }

  // Only the fields handled by ha-form
  _formData() {
    return {
      title:             this._config.title             ?? "",
      expensive_hours:   this._config.expensive_hours    ?? 3,
      show_price_labels: this._config.show_price_labels ?? false,
      label_width:       this._config.label_width        ?? 120,
      status_entity:     this._config.status_entity      ?? "",
    };
  }

  _build() {
    const root = this.shadowRoot;

    const style = document.createElement("style");
    style.textContent = `
      .sec { font-size:12px; font-weight:600; color:var(--secondary-text-color);
        text-transform:uppercase; letter-spacing:.8px; padding:16px 0 8px; }
      .dev-row { display:flex; align-items:center; gap:8px; margin-bottom:6px; }
      .dev-id  { font-size:12px; color:var(--secondary-text-color); flex:1;
        overflow:hidden; text-overflow:ellipsis; white-space:nowrap; min-width:0; }
    `;
    root.appendChild(style);

    const schema = [
      { name: "title",             label: "editor_title",             selector: { text: {} } },
      { name: "expensive_hours",   label: "editor_expensive_hours",   selector: { number: { min: 0, max: 12, step: 1, mode: "slider" } } },
      { name: "show_price_labels", label: "editor_show_price_labels", selector: { boolean: {} } },
      { name: "label_width",       label: "editor_label_width",       selector: { number: { min: 60, max: 300, step: 10, mode: "box" } } },
      { name: "status_entity",     label: "editor_status_entity",     selector: { entity: { domain: "sensor" } } },
    ];

    const form = document.createElement("ha-form");
    form.hass         = this._hass;
    form.data         = this._formData();
    form.schema       = schema;
    form.computeLabel = (s) => _t(this._hass?.locale?.language || "en", s.label);

    form.addEventListener("value-changed", (e) => {
      const v = e.detail.value;
      this._config = { ...this._config };
      if (v.title)             this._config.title             = v.title;          else delete this._config.title;
      this._config.expensive_hours   = v.expensive_hours;
      this._config.show_price_labels = v.show_price_labels;
      this._config.label_width       = v.label_width;
      if (v.status_entity)     this._config.status_entity     = v.status_entity;  else delete this._config.status_entity;
      this._fire();
      // Refresh device list if status_entity changed
      this._renderDeviceNames();
    });

    this._form = form;
    root.appendChild(form);

    // ── Device names section ─────────────────────────────────────────────────
    const secTitle = document.createElement("div");
    secTitle.className = "sec";
    this._secTitle = secTitle;
    root.appendChild(secTitle);

    const container = document.createElement("div");
    this._namesContainer = container;
    root.appendChild(container);

    this._renderDeviceNames();
  }

  _renderDeviceNames() {
    if (!this._namesContainer) return;
    const lang    = this._hass?.locale?.language || "en";
    const devices = this._devices();
    const container = this._namesContainer;
    container.innerHTML = "";

    if (this._secTitle) this._secTitle.textContent = _t(lang, "editor_device_names");

    if (!devices.length) {
      const msg = document.createElement("div");
      msg.style.cssText = "font-size:13px;color:var(--disabled-text-color);padding:2px 0 10px";
      msg.textContent = _t(lang, "editor_no_devices");
      container.appendChild(msg);
      return;
    }

    for (const devId of devices) {
      const row = document.createElement("div");
      row.className = "dev-row";

      const lbl = document.createElement("div");
      lbl.className   = "dev-id";
      lbl.textContent = this._hass?.states?.[devId]?.attributes?.friendly_name ?? devId;
      lbl.title       = devId;

      const field = document.createElement("ha-textfield");
      field.label       = _t(lang, "editor_device_placeholder");
      field.value       = this._config.device_names?.[devId] ?? "";
      field.placeholder = devId.split(".").pop().replace(/_/g, " ");
      field.style.cssText = "flex:1;min-width:0";

      const onUpdate = () => {
        const val = field.value.trim();
        if (!this._config.device_names) this._config.device_names = {};
        if (val) this._config.device_names[devId] = val;
        else     delete this._config.device_names[devId];
        if (!Object.keys(this._config.device_names).length) delete this._config.device_names;
        this._fire();
      };
      field.addEventListener("change", onUpdate);

      row.append(lbl, field);
      container.appendChild(row);
    }
  }

  _fire() {
    this.dispatchEvent(new CustomEvent("config-changed", {
      detail: { config: { ...this._config } },
      bubbles: true,
      composed: true,
    }));
  }
}

customElements.define("spot-scheduler-card-editor", SpotSchedulerCardEditor);
customElements.define("spot-scheduler-card", SpotSchedulerCard);

window.customCards = window.customCards || [];
window.customCards.push({
  type: "spot-scheduler-card",
  name: "Spot Scheduler",
  description: "Run your appliances when electricity is cheapest — Nord Pool-powered scheduling that can automatically pick the cheapest hours and executes them on time.",
  preview: true,
});
