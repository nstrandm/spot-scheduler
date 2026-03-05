<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 860 480" width="860" height="480">
  <defs>
    <style>
      text { font-family: 'Segoe UI', system-ui, sans-serif; }
    </style>
    <linearGradient id="cardBg" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#1e2538"/>
      <stop offset="100%" stop-color="#1a1f2e"/>
    </linearGradient>
  </defs>

  <!-- Card background -->
  <rect width="860" height="480" rx="16" fill="#0d1117"/>
  <rect x="12" y="12" width="836" height="456" rx="14" fill="url(#cardBg)" stroke="#2a3348" stroke-width="1"/>

  <!-- Header -->
  <text x="32" y="52" fill="#ffffff" font-size="18" font-weight="700">⚡ SpotScheduler</text>
  <text x="32" y="70" fill="#4a5568" font-size="11">Hourly device schedule · Nord Pool spot prices</text>

  <!-- Min/Max stat boxes -->
  <rect x="680" y="28" width="76" height="48" rx="9" fill="#242b3d"/>
  <text x="718" y="48" fill="#4a5568" font-size="9" text-anchor="middle" font-weight="600">MIN</text>
  <text x="718" y="66" fill="#4ade80" font-size="13" text-anchor="middle" font-weight="700">2.1 c</text>

  <rect x="764" y="28" width="76" height="48" rx="9" fill="#242b3d"/>
  <text x="802" y="48" fill="#4a5568" font-size="9" text-anchor="middle" font-weight="600">MAX</text>
  <text x="802" y="66" fill="#f87171" font-size="13" text-anchor="middle" font-weight="700">18.7 c</text>

  <!-- Date nav -->
  <rect x="32" y="88" width="22" height="22" rx="5" fill="#242b3d"/>
  <text x="43" y="103" fill="#8896b3" font-size="11" text-anchor="middle">◀</text>
  <text x="170" y="103" fill="#c8d3e8" font-size="13" font-weight="600" text-anchor="middle">Thursday, 5 Mar 2026</text>
  <rect x="298" y="88" width="22" height="22" rx="5" fill="#242b3d"/>
  <text x="309" y="103" fill="#8896b3" font-size="11" text-anchor="middle">▶</text>
  <text x="730" y="103" fill="#3d4f6e" font-size="10">✓ Prices updated (tomorrow_valid)</text>

  <!-- Legend -->
  <circle cx="40" cy="124" r="5" fill="#1d6fa8" stroke="#60a5fa" stroke-width="1.5"/>
  <text x="50" y="128" fill="#8896b3" font-size="11">On</text>
  <circle cx="85" cy="124" r="5" fill="#252d3f" stroke="#3a4560" stroke-width="1.5"/>
  <text x="95" y="128" fill="#8896b3" font-size="11">Off</text>
  <circle cx="130" cy="124" r="5" fill="#1c2234" stroke="#f87171" stroke-width="1.5"/>
  <text x="140" y="128" fill="#8896b3" font-size="11">Expensive (top 3)</text>
  <circle cx="250" cy="124" r="5" fill="none" stroke="#60a5fa" stroke-width="2"/>
  <text x="260" y="128" fill="#8896b3" font-size="11">Current hour</text>

  <!-- Price bars -->
  <text x="32" y="148" fill="#4a5568" font-size="10">Avg price (€/kWh) · 15 min slots → hourly average</text>

  <!-- 24 price bars -->
  <g transform="translate(32, 155)">
    <!-- bar data: [height, color, isExpensive] for hours 0-23 -->
    <!-- hour 0-5: cheap night -->
    <g transform="translate(0,0)">
      <rect x="0" y="30" width="28" height="12" rx="2" fill="#32c850"/>
      <text x="14" y="52" fill="#3d4f6e" font-size="7" text-anchor="middle">0</text>
    </g>
    <g transform="translate(33,0)">
      <rect x="0" y="32" width="28" height="10" rx="2" fill="#35d04e"/>
      <text x="14" y="52" fill="#3d4f6e" font-size="7" text-anchor="middle">1</text>
    </g>
    <g transform="translate(66,0)">
      <rect x="0" y="34" width="28" height="8" rx="2" fill="#38d84c"/>
      <text x="14" y="52" fill="#3d4f6e" font-size="7" text-anchor="middle">2</text>
    </g>
    <g transform="translate(99,0)">
      <rect x="0" y="36" width="28" height="6" rx="2" fill="#3bdf4a"/>
      <text x="14" y="52" fill="#3d4f6e" font-size="7" text-anchor="middle">3</text>
    </g>
    <g transform="translate(132,0)">
      <rect x="0" y="35" width="28" height="7" rx="2" fill="#3bdf4a"/>
      <text x="14" y="52" fill="#3d4f6e" font-size="7" text-anchor="middle">4</text>
    </g>
    <g transform="translate(165,0)">
      <rect x="0" y="30" width="28" height="12" rx="2" fill="#50d040"/>
      <text x="14" y="52" fill="#3d4f6e" font-size="7" text-anchor="middle">5</text>
    </g>
    <!-- hour 6-11: morning ramp -->
    <g transform="translate(198,0)">
      <rect x="0" y="22" width="28" height="20" rx="2" fill="#90c030"/>
      <text x="14" y="52" fill="#3d4f6e" font-size="7" text-anchor="middle">6</text>
    </g>
    <!-- hour 7: expensive -->
    <g transform="translate(231,0)">
      <rect x="0" y="8" width="28" height="34" rx="2" fill="#e06020" filter="drop-shadow(0 0 3px rgba(248,113,113,0.6))"/>
      <rect x="-1" y="7" width="30" height="36" rx="3" fill="none" stroke="#f87171" stroke-width="1.5"/>
      <text x="14" y="52" fill="#3d4f6e" font-size="7" text-anchor="middle">7</text>
    </g>
    <g transform="translate(264,0)">
      <rect x="0" y="4" width="28" height="38" rx="2" fill="#d05020"/>
      <text x="14" y="52" fill="#3d4f6e" font-size="7" text-anchor="middle">8</text>
    </g>
    <g transform="translate(297,0)">
      <rect x="0" y="6" width="28" height="36" rx="2" fill="#d05525"/>
      <text x="14" y="52" fill="#3d4f6e" font-size="7" text-anchor="middle">9</text>
    </g>
    <g transform="translate(330,0)">
      <rect x="0" y="10" width="28" height="32" rx="2" fill="#c06030"/>
      <text x="14" y="52" fill="#3d4f6e" font-size="7" text-anchor="middle">10</text>
    </g>
    <g transform="translate(363,0)">
      <rect x="0" y="14" width="28" height="28" rx="2" fill="#b07030"/>
      <text x="14" y="52" fill="#3d4f6e" font-size="7" text-anchor="middle">11</text>
    </g>
    <!-- hour 12-14: midday -->
    <g transform="translate(396,0)">
      <rect x="0" y="18" width="28" height="24" rx="2" fill="#a08030"/>
      <text x="14" y="52" fill="#3d4f6e" font-size="7" text-anchor="middle">12</text>
    </g>
    <g transform="translate(429,0)">
      <rect x="0" y="20" width="28" height="22" rx="2" fill="#a08530"/>
      <text x="14" y="52" fill="#3d4f6e" font-size="7" text-anchor="middle">13</text>
    </g>
    <g transform="translate(462,0)">
      <rect x="0" y="18" width="28" height="24" rx="2" fill="#a07830"/>
      <text x="14" y="52" fill="#3d4f6e" font-size="7" text-anchor="middle">14</text>
    </g>
    <!-- hour 15: current -->
    <g transform="translate(495,0)">
      <rect x="0" y="17" width="28" height="25" rx="2" fill="#a07030"/>
      <rect x="-2" y="15" width="32" height="29" rx="4" fill="none" stroke="#60a5fa" stroke-width="2"/>
      <text x="14" y="52" fill="#60a5fa" font-size="7" text-anchor="middle" font-weight="800">15</text>
    </g>
    <g transform="translate(528,0)">
      <rect x="0" y="15" width="28" height="27" rx="2" fill="#b06828"/>
      <text x="14" y="52" fill="#3d4f6e" font-size="7" text-anchor="middle">16</text>
    </g>
    <g transform="translate(561,0)">
      <rect x="0" y="12" width="28" height="30" rx="2" fill="#c05820"/>
      <text x="14" y="52" fill="#3d4f6e" font-size="7" text-anchor="middle">17</text>
    </g>
    <!-- hour 18: expensive -->
    <g transform="translate(594,0)">
      <rect x="0" y="2" width="28" height="40" rx="2" fill="#e03010" filter="drop-shadow(0 0 3px rgba(248,113,113,0.6))"/>
      <rect x="-1" y="1" width="30" height="42" rx="3" fill="none" stroke="#f87171" stroke-width="1.5"/>
      <text x="14" y="52" fill="#3d4f6e" font-size="7" text-anchor="middle">18</text>
    </g>
    <!-- hour 19: expensive -->
    <g transform="translate(627,0)">
      <rect x="0" y="0" width="28" height="42" rx="2" fill="#e82808" filter="drop-shadow(0 0 3px rgba(248,113,113,0.7))"/>
      <rect x="-1" y="-1" width="30" height="44" rx="3" fill="none" stroke="#f87171" stroke-width="1.5"/>
      <text x="14" y="52" fill="#3d4f6e" font-size="7" text-anchor="middle">19</text>
    </g>
    <g transform="translate(660,0)">
      <rect x="0" y="8" width="28" height="34" rx="2" fill="#d04018"/>
      <text x="14" y="52" fill="#3d4f6e" font-size="7" text-anchor="middle">20</text>
    </g>
    <g transform="translate(693,0)">
      <rect x="0" y="16" width="28" height="26" rx="2" fill="#b06025"/>
      <text x="14" y="52" fill="#3d4f6e" font-size="7" text-anchor="middle">21</text>
    </g>
    <g transform="translate(726,0)">
      <rect x="0" y="24" width="28" height="18" rx="2" fill="#808035"/>
      <text x="14" y="52" fill="#3d4f6e" font-size="7" text-anchor="middle">22</text>
    </g>
    <g transform="translate(759,0)">
      <rect x="0" y="28" width="28" height="14" rx="2" fill="#50a038"/>
      <text x="14" y="52" fill="#3d4f6e" font-size="7" text-anchor="middle">23</text>
    </g>
  </g>

  <!-- Divider -->
  <line x1="32" y1="228" x2="828" y2="228" stroke="#242b3d" stroke-width="1"/>

  <!-- Grid header row -->
  <g transform="translate(32, 242)" fill="#3d4f6e" font-size="8" font-weight="700" text-anchor="middle">
    <text x="190">0</text><text x="223">1</text><text x="256">2</text><text x="289">3</text>
    <text x="322">4</text><text x="355">5</text><text x="388">6</text><text x="421">7</text>
    <text x="454">8</text><text x="487">9</text><text x="520">10</text><text x="553">11</text>
    <text x="586">12</text><text x="619">13</text><text x="652">14</text>
    <text x="685" fill="#60a5fa" font-weight="800">15</text>
    <text x="718">16</text><text x="751">17</text><text x="784">18</text><text x="817">19</text>
  </g>

  <!-- Device row 1: Washing Machine -->
  <text x="32" y="275" fill="#c8d3e8" font-size="11" font-weight="600">Washing machine</text>
  <!-- cells h0-h4: ON (blue) -->
  <g transform="translate(176,258)">
    <rect width="24" height="22" rx="4" fill="#1d6fa8" stroke="#60a5fa" stroke-width="1.5"/>
    <text x="12" y="15" fill="#a8d4ff" font-size="9" text-anchor="middle" font-weight="700">✓</text>
  </g>
  <g transform="translate(209,258)">
    <rect width="24" height="22" rx="4" fill="#1d6fa8" stroke="#60a5fa" stroke-width="1.5"/>
    <text x="12" y="15" fill="#a8d4ff" font-size="9" text-anchor="middle" font-weight="700">✓</text>
  </g>
  <g transform="translate(242,258)">
    <rect width="24" height="22" rx="4" fill="#1d6fa8" stroke="#60a5fa" stroke-width="1.5"/>
    <text x="12" y="15" fill="#a8d4ff" font-size="9" text-anchor="middle" font-weight="700">✓</text>
  </g>
  <g transform="translate(275,258)">
    <rect width="24" height="22" rx="4" fill="#1d6fa8" stroke="#60a5fa" stroke-width="1.5"/>
    <text x="12" y="15" fill="#a8d4ff" font-size="9" text-anchor="middle" font-weight="700">✓</text>
  </g>
  <!-- h5-h6: unset -->
  <g transform="translate(308,258)"><rect width="24" height="22" rx="4" fill="#1c2234" stroke="#252d3f" stroke-width="1.5"/></g>
  <g transform="translate(341,258)"><rect width="24" height="22" rx="4" fill="#1c2234" stroke="#252d3f" stroke-width="1.5"/></g>
  <!-- h7: OFF + expensive -->
  <g transform="translate(374,258)">
    <rect width="24" height="22" rx="4" fill="#252d3f" stroke="#f87171" stroke-width="1.5"/>
    <text x="12" y="15" fill="#4a5568" font-size="9" text-anchor="middle" font-weight="700">✕</text>
  </g>
  <!-- h8-h17: OFF or unset -->
  <g transform="translate(407,258)"><rect width="24" height="22" rx="4" fill="#252d3f" stroke="#2e3a52" stroke-width="1.5"/><text x="12" y="15" fill="#4a5568" font-size="9" text-anchor="middle" font-weight="700">✕</text></g>
  <g transform="translate(440,258)"><rect width="24" height="22" rx="4" fill="#1c2234" stroke="#252d3f" stroke-width="1.5"/></g>
  <g transform="translate(473,258)"><rect width="24" height="22" rx="4" fill="#1c2234" stroke="#252d3f" stroke-width="1.5"/></g>
  <g transform="translate(506,258)"><rect width="24" height="22" rx="4" fill="#1c2234" stroke="#252d3f" stroke-width="1.5"/></g>
  <g transform="translate(539,258)"><rect width="24" height="22" rx="4" fill="#1c2234" stroke="#252d3f" stroke-width="1.5"/></g>
  <g transform="translate(572,258)"><rect width="24" height="22" rx="4" fill="#1c2234" stroke="#252d3f" stroke-width="1.5"/></g>
  <g transform="translate(605,258)"><rect width="24" height="22" rx="4" fill="#1c2234" stroke="#252d3f" stroke-width="1.5"/></g>
  <g transform="translate(638,258)"><rect width="24" height="22" rx="4" fill="#1c2234" stroke="#252d3f" stroke-width="1.5"/></g>
  <!-- h15: current hour, unset -->
  <g transform="translate(671,258)"><rect width="24" height="22" rx="4" fill="#1c2234" stroke="#60a5fa" stroke-width="2"/></g>
  <g transform="translate(704,258)"><rect width="24" height="22" rx="4" fill="#1c2234" stroke="#252d3f" stroke-width="1.5"/></g>
  <!-- h18,19: OFF + expensive -->
  <g transform="translate(737,258)"><rect width="24" height="22" rx="4" fill="#1c2234" stroke="#252d3f" stroke-width="1.5"/></g>
  <g transform="translate(770,258)"><rect width="24" height="22" rx="4" fill="#252d3f" stroke="#f87171" stroke-width="1.5"/><text x="12" y="15" fill="#4a5568" font-size="9" text-anchor="middle" font-weight="700">✕</text></g>
  <g transform="translate(803,258)"><rect width="24" height="22" rx="4" fill="#252d3f" stroke="#f87171" stroke-width="1.5"/><text x="12" y="15" fill="#4a5568" font-size="9" text-anchor="middle" font-weight="700">✕</text></g>

  <!-- Device row 2: EV Charger -->
  <text x="32" y="310" fill="#c8d3e8" font-size="11" font-weight="600">EV charger</text>
  <g transform="translate(176,293)"><rect width="24" height="22" rx="4" fill="#1d6fa8" stroke="#60a5fa" stroke-width="1.5"/><text x="12" y="15" fill="#a8d4ff" font-size="9" text-anchor="middle" font-weight="700">✓</text></g>
  <g transform="translate(209,293)"><rect width="24" height="22" rx="4" fill="#1d6fa8" stroke="#60a5fa" stroke-width="1.5"/><text x="12" y="15" fill="#a8d4ff" font-size="9" text-anchor="middle" font-weight="700">✓</text></g>
  <g transform="translate(242,293)"><rect width="24" height="22" rx="4" fill="#1d6fa8" stroke="#60a5fa" stroke-width="1.5"/><text x="12" y="15" fill="#a8d4ff" font-size="9" text-anchor="middle" font-weight="700">✓</text></g>
  <g transform="translate(275,293)"><rect width="24" height="22" rx="4" fill="#1d6fa8" stroke="#60a5fa" stroke-width="1.5"/><text x="12" y="15" fill="#a8d4ff" font-size="9" text-anchor="middle" font-weight="700">✓</text></g>
  <g transform="translate(308,293)"><rect width="24" height="22" rx="4" fill="#1d6fa8" stroke="#60a5fa" stroke-width="1.5"/><text x="12" y="15" fill="#a8d4ff" font-size="9" text-anchor="middle" font-weight="700">✓</text></g>
  <g transform="translate(341,293)"><rect width="24" height="22" rx="4" fill="#1c2234" stroke="#252d3f" stroke-width="1.5"/></g>
  <g transform="translate(374,293)"><rect width="24" height="22" rx="4" fill="#252d3f" stroke="#f87171" stroke-width="1.5"/><text x="12" y="15" fill="#4a5568" font-size="9" text-anchor="middle" font-weight="700">✕</text></g>
  <g transform="translate(407,293)"><rect width="24" height="22" rx="4" fill="#1c2234" stroke="#252d3f" stroke-width="1.5"/></g>
  <g transform="translate(440,293)"><rect width="24" height="22" rx="4" fill="#1c2234" stroke="#252d3f" stroke-width="1.5"/></g>
  <g transform="translate(473,293)"><rect width="24" height="22" rx="4" fill="#1c2234" stroke="#252d3f" stroke-width="1.5"/></g>
  <g transform="translate(506,293)"><rect width="24" height="22" rx="4" fill="#1c2234" stroke="#252d3f" stroke-width="1.5"/></g>
  <g transform="translate(539,293)"><rect width="24" height="22" rx="4" fill="#1c2234" stroke="#252d3f" stroke-width="1.5"/></g>
  <g transform="translate(572,293)"><rect width="24" height="22" rx="4" fill="#1c2234" stroke="#252d3f" stroke-width="1.5"/></g>
  <g transform="translate(605,293)"><rect width="24" height="22" rx="4" fill="#1c2234" stroke="#252d3f" stroke-width="1.5"/></g>
  <g transform="translate(638,293)"><rect width="24" height="22" rx="4" fill="#1c2234" stroke="#252d3f" stroke-width="1.5"/></g>
  <g transform="translate(671,293)"><rect width="24" height="22" rx="4" fill="#1c2234" stroke="#60a5fa" stroke-width="2"/></g>
  <g transform="translate(704,293)"><rect width="24" height="22" rx="4" fill="#1c2234" stroke="#252d3f" stroke-width="1.5"/></g>
  <g transform="translate(737,293)"><rect width="24" height="22" rx="4" fill="#1c2234" stroke="#252d3f" stroke-width="1.5"/></g>
  <g transform="translate(770,293)"><rect width="24" height="22" rx="4" fill="#252d3f" stroke="#f87171" stroke-width="1.5"/><text x="12" y="15" fill="#4a5568" font-size="9" text-anchor="middle" font-weight="700">✕</text></g>
  <g transform="translate(803,293)"><rect width="24" height="22" rx="4" fill="#252d3f" stroke="#f87171" stroke-width="1.5"/><text x="12" y="15" fill="#4a5568" font-size="9" text-anchor="middle" font-weight="700">✕</text></g>

  <!-- Device row 3: Floor heating -->
  <text x="32" y="345" fill="#c8d3e8" font-size="11" font-weight="600">Floor heating</text>
  <g transform="translate(176,328)"><rect width="24" height="22" rx="4" fill="#1d6fa8" stroke="#60a5fa" stroke-width="1.5"/><text x="12" y="15" fill="#a8d4ff" font-size="9" text-anchor="middle" font-weight="700">✓</text></g>
  <g transform="translate(209,328)"><rect width="24" height="22" rx="4" fill="#1d6fa8" stroke="#60a5fa" stroke-width="1.5"/><text x="12" y="15" fill="#a8d4ff" font-size="9" text-anchor="middle" font-weight="700">✓</text></g>
  <g transform="translate(242,328)"><rect width="24" height="22" rx="4" fill="#1d6fa8" stroke="#60a5fa" stroke-width="1.5"/><text x="12" y="15" fill="#a8d4ff" font-size="9" text-anchor="middle" font-weight="700">✓</text></g>
  <g transform="translate(275,328)"><rect width="24" height="22" rx="4" fill="#1d6fa8" stroke="#60a5fa" stroke-width="1.5"/><text x="12" y="15" fill="#a8d4ff" font-size="9" text-anchor="middle" font-weight="700">✓</text></g>
  <g transform="translate(308,328)"><rect width="24" height="22" rx="4" fill="#1d6fa8" stroke="#60a5fa" stroke-width="1.5"/><text x="12" y="15" fill="#a8d4ff" font-size="9" text-anchor="middle" font-weight="700">✓</text></g>
  <g transform="translate(341,328)"><rect width="24" height="22" rx="4" fill="#1d6fa8" stroke="#60a5fa" stroke-width="1.5"/><text x="12" y="15" fill="#a8d4ff" font-size="9" text-anchor="middle" font-weight="700">✓</text></g>
  <g transform="translate(374,328)"><rect width="24" height="22" rx="4" fill="#252d3f" stroke="#f87171" stroke-width="1.5"/><text x="12" y="15" fill="#4a5568" font-size="9" text-anchor="middle" font-weight="700">✕</text></g>
  <g transform="translate(407,328)"><rect width="24" height="22" rx="4" fill="#252d3f" stroke="#2e3a52" stroke-width="1.5"/><text x="12" y="15" fill="#4a5568" font-size="9" text-anchor="middle" font-weight="700">✕</text></g>
  <g transform="translate(440,328)"><rect width="24" height="22" rx="4" fill="#1c2234" stroke="#252d3f" stroke-width="1.5"/></g>
  <g transform="translate(473,328)"><rect width="24" height="22" rx="4" fill="#1c2234" stroke="#252d3f" stroke-width="1.5"/></g>
  <g transform="translate(506,328)"><rect width="24" height="22" rx="4" fill="#1c2234" stroke="#252d3f" stroke-width="1.5"/></g>
  <g transform="translate(539,328)"><rect width="24" height="22" rx="4" fill="#1c2234" stroke="#252d3f" stroke-width="1.5"/></g>
  <g transform="translate(572,328)"><rect width="24" height="22" rx="4" fill="#1c2234" stroke="#252d3f" stroke-width="1.5"/></g>
  <g transform="translate(605,328)"><rect width="24" height="22" rx="4" fill="#1c2234" stroke="#252d3f" stroke-width="1.5"/></g>
  <g transform="translate(638,328)"><rect width="24" height="22" rx="4" fill="#1c2234" stroke="#252d3f" stroke-width="1.5"/></g>
  <g transform="translate(671,328)"><rect width="24" height="22" rx="4" fill="#1d6fa8" stroke="#60a5fa" stroke-width="2"/><text x="12" y="15" fill="#a8d4ff" font-size="9" text-anchor="middle" font-weight="700">✓</text></g>
  <g transform="translate(704,328)"><rect width="24" height="22" rx="4" fill="#1d6fa8" stroke="#60a5fa" stroke-width="1.5"/><text x="12" y="15" fill="#a8d4ff" font-size="9" text-anchor="middle" font-weight="700">✓</text></g>
  <g transform="translate(737,328)"><rect width="24" height="22" rx="4" fill="#1d6fa8" stroke="#60a5fa" stroke-width="1.5"/><text x="12" y="15" fill="#a8d4ff" font-size="9" text-anchor="middle" font-weight="700">✓</text></g>
  <g transform="translate(770,328)"><rect width="24" height="22" rx="4" fill="#252d3f" stroke="#f87171" stroke-width="1.5"/><text x="12" y="15" fill="#4a5568" font-size="9" text-anchor="middle" font-weight="700">✕</text></g>
  <g transform="translate(803,328)"><rect width="24" height="22" rx="4" fill="#252d3f" stroke="#f87171" stroke-width="1.5"/><text x="12" y="15" fill="#4a5568" font-size="9" text-anchor="middle" font-weight="700">✕</text></g>

  <!-- Save hint -->
  <text x="828" y="465" fill="#3d4f6e" font-size="10" text-anchor="end" font-style="italic">✓ Changes saved automatically to Home Assistant</text>
</svg>
