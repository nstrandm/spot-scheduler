// SpotScheduler – Lovelace Custom Card
// Language is taken from hass.locale.language (set in HA user profile)
// Supported: en, fi  |  Falls back to English for unknown languages.

const TRANSLATIONS = {
  en: {
    title: "SpotScheduler",
    subtitle: "Hourly device schedule · Nord Pool spot prices",
    prices_note: "Prices fetched automatically when available",
    prices_pending: "⏳ Waiting for today's prices from Nord Pool",
    on: "On",
    off: "Off",
    unset: "–",
    legend_on: "On",
    legend_off: "Off",
    legend_expensive: "Expensive (top {n})",
    legend_current: "Current hour",
    stat_min: "Min",
    stat_max: "Max",
    price_row_label: "Avg price (€/kWh) · 15 min slots → hourly average",
    no_devices: "No devices configured.",
    save_hint: "✓ Changes saved automatically to Home Assistant",
  },
  fi: {
    title: "SpotScheduler",
    subtitle: "Tuntiaikataulu · Nord Pool pörssisähkö",
    prices_note: "Hinnat haetaan automaattisesti kun saatavilla",
    prices_pending: "⏳ Odotetaan päivän hintoja Nord Poolilta",
    on: "Päällä",
    off: "Pois",
    unset: "–",
    legend_on: "Päällä",
    legend_off: "Pois",
    legend_expensive: "Kallis ({n} kalleinta)",
    legend_current: "Nykyinen tunti",
    stat_min: "Min",
    stat_max: "Max",
    price_row_label: "Tunnin keskihinta (€/kWh) · 15 min arvoista laskettu",
    no_devices: "Ei laitteita konfiguroitu.",
    save_hint: "✓ Muutokset tallentuvat automaattisesti Home Assistantiin",
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
    box-shadow: var(--ha-card-box-shadow, var(--material-shadow-elevation-2dp)); }
  .header { display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:18px; }
  .title { font-size:17px; font-weight:700; color:var(--primary-text-color); }
  .subtitle { font-size:11px; color:var(--secondary-text-color); margin-top:3px; }
  .stats { display:flex; gap:9px; }
  .stat-box { background:var(--secondary-background-color); border-radius:9px;
    padding:7px 13px; text-align:center; min-width:72px; }
  .stat-label { font-size:9px; color:var(--secondary-text-color);
    text-transform:uppercase; letter-spacing:.8px; }
  .stat-value { font-size:13px; font-weight:700; margin-top:2px; }
  .stat-value.min { color:var(--success-color, #4ade80); }
  .stat-value.max { color:var(--error-color, #f87171); }
  .date-nav { display:flex; align-items:center; gap:9px; margin-bottom:14px; }
  .date-btn { background:var(--secondary-background-color); border:none;
    color:var(--secondary-text-color); width:28px; height:28px;
    border-radius:6px; cursor:pointer; font-size:13px;
    display:flex; align-items:center; justify-content:center; }
  .date-btn:hover { filter:brightness(1.15); }
  .date-btn:disabled { opacity:0.3; cursor:default; filter:none; }
  .date-lbl { font-size:13px; font-weight:600; color:var(--primary-text-color); }
  .prices-note { font-size:10px; color:var(--disabled-text-color); margin-left:auto; }
  .legend { display:flex; gap:13px; flex-wrap:wrap; margin-bottom:14px; }
  .leg-item { display:flex; align-items:center; gap:6px;
    font-size:11px; color:var(--secondary-text-color); }
  .leg-dot { width:10px; height:10px; border-radius:50%; flex-shrink:0; }
  .price-section { margin-bottom:14px; }
  .price-lbl { font-size:10px; color:var(--disabled-text-color); margin-bottom:5px; }
  .bars { display:flex; align-items:flex-end; gap:2px; height:52px; }
  .bar-col { flex:1; display:flex; flex-direction:column; align-items:center; justify-content:flex-end; height:100%; }
  .bar { width:100%; border-radius:2px 2px 0 0; min-height:2px; }
  .bar.exp { box-shadow:0 0 5px color-mix(in srgb, var(--error-color, #f87171) 65%, transparent); }
  .bar-h { font-size:7px; color:var(--disabled-text-color); margin-top:3px; }
  .bar-h.cur { color:var(--primary-color); font-weight:800; }
  .divider { height:1px; background:var(--divider-color); margin:13px 0; }
  .grid-scroll { overflow-x:auto; }
  .gh { text-align:center; font-size:8px; color:var(--disabled-text-color);
    font-weight:700; padding:2px 0; }
  .gh.cur { color:var(--primary-color); }
  .dev-lbl { font-size:11px; font-weight:600; color:var(--primary-text-color);
    display:flex; align-items:center; padding-right:5px;
    white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
  .cell { aspect-ratio:1; border-radius:4px; border:1.5px solid transparent;
    display:flex; align-items:center; justify-content:center;
    font-size:9px; font-weight:700; cursor:pointer; min-height:20px;
    transition:transform .1s; }
  .cell:hover { transform:scale(1.15); z-index:5; position:relative; }
  .cell.on { background:var(--primary-color); border-color:var(--primary-color);
    color:var(--text-primary-color, #fff);
    box-shadow:0 0 6px color-mix(in srgb, var(--primary-color) 45%, transparent); }
  .cell.off { background:var(--secondary-background-color);
    border-color:var(--divider-color); color:var(--disabled-text-color); }
  .cell.unset { background:var(--ha-card-background, var(--card-background-color));
    border-color:var(--divider-color); }
  .cell.exp-cell { border-color:var(--error-color, #f87171) !important; }
  .cell.cur-cell { box-shadow:0 0 0 2px var(--primary-color); }
  .no-prices { text-align:center; padding:20px; color:var(--disabled-text-color);
    font-size:13px; }
  .save-hint { text-align:right; font-size:10px; color:var(--disabled-text-color);
    margin-top:11px; font-style:italic; }
`;

// ── Helpers ───────────────────────────────────────────────────────────────────

function _todayISO() { return new Date().toISOString().split("T")[0]; }

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
    const tomorrow = (() => { const d = new Date(); d.setDate(d.getDate()+1); return d.toISOString().split("T")[0]; })();

    const todayPrices    = attrs.prices ?? {};
    const tomorrowPrices = attrs.prices_tomorrow ?? {};

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
    if (attrs.schedules) this._schedules = { ...this._schedules, ...attrs.schedules };
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
  }

  _findStatusEntity() {
    if (!this._hass) return null;
    return Object.keys(this._hass.states).find(
      id => id.startsWith("sensor.") &&
            id.includes("spot_scheduler") &&
            id.includes("schedule_status")
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
    const prices = this._prices[this._selectedDate] ?? this._prices[today] ?? {};
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
    const next = cur === true ? false : true;

    if (!this._schedules[this._selectedDate]) this._schedules[this._selectedDate] = {};
    if (!this._schedules[this._selectedDate][deviceId]) this._schedules[this._selectedDate][deviceId] = {};
    this._schedules[this._selectedDate][deviceId][String(hour)] = next;
    this._update();

    if (!this._hass) return;

    this._hass.callService("spot_scheduler", "set_device_schedule", {
      date: this._selectedDate,
      hour,
      device_id: deviceId,
      enabled: next,
    }).catch(() => {
      this._schedules[this._selectedDate][deviceId][String(hour)] = cur;
      this._update();
    });
  }

  _priceColor(price) {
    const min = this._minPrice ?? 0;
    const max = this._maxPrice ?? 0.2;
    const range = max - min;
    if (!range) return "#a0c4ff";
    const r = Math.max(0, Math.min(1, (price - min) / range));
    if (r < 0.35) return `rgb(50,${Math.round(200 + 55 * (1 - r / 0.35))},70)`;
    if (r < 0.65) { const t2 = (r - 0.35) / 0.3; return `rgb(${Math.round(200 + 55 * t2)},${Math.round(200 - 80 * t2)},50)`; }
    const t2 = (r - 0.65) / 0.35; return `rgb(${Math.round(230 + 25 * t2)},${Math.round(80 - 50 * t2)},50)`;
  }

  _fmtPrice(p) {
    if (p == null) return "–";
    return (p * 100).toFixed(2) + " c/kWh";
  }

  _canGoPrev() {
    const today = new Date(_todayISO() + "T12:00:00");
    const minDate = new Date(today); minDate.setDate(minDate.getDate() - 7);
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
      { style: "background:var(--ha-card-background,var(--card-background-color));border:1.5px solid var(--error-color,#f87171)", key: "legend_expensive" },
      { style: "border:2px solid var(--primary-color);background:transparent", key: "legend_current" },
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

    // ── Price bars ────────────────────────────────────────────────────────────
    const priceSection = _el("div", "price-section");
    const priceLbl = _el("div", "price-lbl");
    const barsContainer = _el("div", "bars");
    priceSection.append(priceLbl, barsContainer);

    const barEls = [];
    for (let h = 0; h < 24; h++) {
      const col = _el("div", "bar-col");
      const bar = _el("div", "bar");
      const label = _el("div", "bar-h", String(h));
      col.append(bar, label);
      barsContainer.appendChild(col);
      barEls.push({ col, bar, label });
    }

    const noPricesMsg = _el("div", "no-prices");
    card.append(priceSection, noPricesMsg);

    // ── Divider ──────────────────────────────────────────────────────────────
    card.appendChild(_el("div", "divider"));

    // ── Schedule grid ────────────────────────────────────────────────────────
    const gridScroll = _el("div", "grid-scroll");
    const devices = this._config.devices ?? [];
    const labelW = this._config.label_width ?? 120;
    const gridCols = `${labelW}px repeat(24, minmax(18px, 1fr))`;

    // Hour header row
    const headerRow = _el("div");
    headerRow.style.cssText = `display:grid;grid-template-columns:${gridCols};gap:2px;margin-bottom:3px`;
    headerRow.appendChild(_el("div"));
    const hourHeaders = [];
    for (let h = 0; h < 24; h++) {
      const gh = _el("div", "gh", String(h));
      headerRow.appendChild(gh);
      hourHeaders.push(gh);
    }
    gridScroll.appendChild(headerRow);

    // Device rows with persistent cells – event listeners bound once here
    const deviceRows = [];
    for (const devId of devices) {
      const name = this._deviceName(devId);
      const row = _el("div");
      row.style.cssText = `display:grid;grid-template-columns:${gridCols};gap:2px;margin-bottom:4px;align-items:center`;
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
    card.appendChild(gridScroll);

    // ── Footer ───────────────────────────────────────────────────────────────
    const saveHint = _el("div", "save-hint");
    card.appendChild(saveHint);

    // Store all mutable references
    this._dom = {
      titleEl, subtitleEl, statsEl, minLabel, minValue, maxLabel, maxValue,
      prevBtn, nextBtn, dateLbl, pricesNote,
      legendSpans,
      priceSection, noPricesMsg, priceLbl, barEls,
      hourHeaders, deviceRows, noDevicesMsg, saveHint,
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
    const maxP = pricesLoaded ? Math.max(...Object.values(dayPrices)) : 0;

    // Header text
    d.titleEl.textContent = this._config.title || this._tr("title");
    d.subtitleEl.textContent = this._tr("subtitle");

    // Stats visibility + values
    if (this._minPrice != null) {
      d.statsEl.style.display = "";
      d.minLabel.textContent = this._tr("stat_min");
      d.minValue.textContent = this._fmtPrice(this._minPrice);
      d.maxLabel.textContent = this._tr("stat_max");
      d.maxValue.textContent = this._fmtPrice(this._maxPrice);
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

      for (let h = 0; h < 24; h++) {
        const { col, bar, label } = d.barEls[h];
        const p = dayPrices[h];
        const barH = p != null ? Math.round((Math.abs(p) / (maxP || 1)) * 48) + 3 : 2;
        const color = p != null ? this._priceColor(p) : "var(--secondary-background-color)";
        const isExp = expHours.has(h);

        bar.style.height = barH + "px";
        bar.style.background = color;
        bar.className = isExp ? "bar exp" : "bar";
        label.className = (isToday && h === curHour) ? "bar-h cur" : "bar-h";
        col.title = `${h}:00 – ${this._fmtPrice(p)}`;
      }
    } else {
      d.priceSection.style.display = "none";
      d.noPricesMsg.style.display = "";
      d.noPricesMsg.textContent = this._tr("prices_pending");
    }

    // Hour column headers
    for (let h = 0; h < 24; h++) {
      d.hourHeaders[h].className = (isToday && h === curHour) ? "gh cur" : "gh";
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
        if (state === true)       { cls += " on";    icon = "✓"; }
        else if (state === false)  { cls += " off";   icon = "✕"; }
        else                       { cls += " unset"; }
        if (isExp) cls += " exp-cell";
        if (isCur) cls += " cur-cell";

        if (el.className !== cls) el.className = cls;
        if (el.textContent !== icon) el.textContent = icon;
        el.title = `${hour}:00 · ${name} · ${this._fmtPrice(dayPrices[hour])}`;
      }
    }

    // No-devices message
    d.noDevicesMsg.style.display = devices.length ? "none" : "";
    d.noDevicesMsg.textContent = this._tr("no_devices");

    // Footer
    d.saveHint.textContent = this._tr("save_hint");
  }

  getCardSize() { return 6; }

  static getStubConfig() {
    return {};
  }
}

customElements.define("spot-scheduler-card", SpotSchedulerCard);

window.customCards = window.customCards || [];
window.customCards.push({
  type: "spot-scheduler-card",
  name: "SpotScheduler",
  description: "Hourly device schedule based on Nord Pool spot electricity prices.",
  preview: true,
});
