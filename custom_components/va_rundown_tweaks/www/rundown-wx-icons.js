// View Assist Rundown Tweaks — shared weather icon set.
//
// One set of animated SVG icons used everywhere Rundown shows weather: the
// full screen page, the small screen (mobile) page, and the View Assist
// clock view's <rundown-tweaks-wx-icon>. Loaded as a classic <script> by
// rundown.html and imported by rundown-wx-icon.js; either way it defines
// globalThis.RundownWxIcons.
//
// Accepts every condition Rundown can be given:
//   • Home Assistant weather conditions (the clock view, and the page's
//     "weather entity" source): sunny, clear-night, partlycloudy, cloudy,
//     fog, hail, lightning, lightning-rainy, pouring, rainy, snowy,
//     snowy-rainy, windy, windy-variant, exceptional
//   • Pirate Weather API icons, standard set: clear-day, clear-night, rain,
//     snow, sleet, wind, fog, cloudy, partly-cloudy-day/night, hail,
//     thunderstorm, tornado, mixed, none
//   • Pirate Weather expanded set (icon=pirate): mostly-clear-*,
//     mostly-cloudy-*, possible-{rain,snow,sleet,precipitation}-*, drizzle,
//     light-rain, heavy-rain, precipitation, flurries, light-snow,
//     heavy-snow, very-light-sleet, light-sleet, heavy-sleet, breezy,
//     dangerous-wind, mist, haze, smoke
// Anything else is matched by keyword (e.g. "freezing-rain" -> sleet), so a
// new upstream name still gets a sensible icon rather than nothing.
//
// Drawing rule: stroke/fill are always set on the drawn shapes or a <g>,
// never on the outer <svg>. Both the page (.wx-svg) and the clock element
// style the outer <svg> with `stroke:none`, and a CSS property there beats
// the element's own presentation attribute — which is exactly why the old
// fog and wind icons rendered blank.
(function (root) {
  "use strict";
  const VERSION = 2;
  if (root.RundownWxIcons && root.RundownWxIcons.version >= VERSION) return;

  const CLOUD_D = "M18 10h-1.26A8 8 0 1 0 9 20h9a5 5 0 0 0 0-10z";
  const CLOUD_SM_D = "M20 14h-1a4 4 0 1 0-7.73-1.47A5 5 0 0 0 12 22h8a4 4 0 0 0 0-8z";
  const WISP_D = "M13 20h7a3 3 0 0 0 0-6 4 4 0 0 0-7.5 1.5A2.3 2.3 0 0 0 13 20z";
  const MOON_D = "M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z";
  const MOON_SM_D = "M16 11.79A7 7 0 1 1 8.21 4 5 5 0 0 0 16 11.79z";
  const LINE = 'fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"';

  const r2 = (n) => Math.round(n * 100) / 100;
  // Evenly spaced rays around (cx, cy) between radii a and b.
  function rays(cx, cy, a, b, count = 8, from = 0, to = 360) {
    const step = (to - from) / (to - from === 360 ? count : count - 1);
    let out = "";
    for (let i = 0; i < count; i++) {
      const t = ((from + i * step) * Math.PI) / 180;
      out += `<line x1="${r2(cx + a * Math.cos(t))}" y1="${r2(cy + a * Math.sin(t))}" x2="${r2(cx + b * Math.cos(t))}" y2="${r2(cy + b * Math.sin(t))}"/>`;
    }
    return out;
  }
  const lines = (pts) => pts.map(([x1, y1, x2, y2]) => `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}"/>`).join("");
  const dots = (pts, r) => pts.map(([x, y]) => `<circle cx="${x}" cy="${y}" r="${r}"/>`).join("");
  const diamond = (x, y, s) => `<path d="M${x} ${y - s}L${x + s} ${y}L${x} ${y + s}L${x - s} ${y}Z"/>`;
  const drop = (x, y) => `<path d="M${x} ${y - 2.1}c.9 1.3 1.45 2.05 1.45 2.7a1.45 1.45 0 0 1-2.9 0c0-.65.55-1.4 1.45-2.7z"/>`;

  // ── Parts ────────────────────────────────────────────────────────────
  const P = {
    // Unchanged from the original Rundown icons.
    sun: `<g class="sw-sun"><circle cx="12" cy="12" r="5" fill="currentColor"/><g ${LINE} stroke-width="2"><line x1="12" y1="1" x2="12" y2="4"/><line x1="12" y1="20" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="6.34" y2="6.34"/><line x1="17.66" y1="17.66" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="4" y2="12"/><line x1="20" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="6.34" y2="17.66"/><line x1="17.66" y1="6.34" x2="19.78" y2="4.22"/></g></g>`,
    moon: `<g class="sw-moon"><path d="${MOON_D}" fill="currentColor"/></g>`,
    sunSmall: `<g class="sw-sun"><circle cx="10" cy="10" r="4" fill="currentColor"/><g ${LINE} stroke-width="1.5"><line x1="10" y1="3" x2="10" y2="5"/><line x1="10" y1="15" x2="10" y2="17"/><line x1="5" y1="5" x2="6.5" y2="6.5"/><line x1="13.5" y1="13.5" x2="15" y2="15"/><line x1="3" y1="10" x2="5" y2="10"/><line x1="15" y1="10" x2="17" y2="10"/><line x1="5" y1="15" x2="6.5" y2="13.5"/><line x1="13.5" y1="6.5" x2="15" y2="5"/></g></g>`,
    moonSmall: `<g class="sw-moon"><path d="${MOON_SM_D}" fill="currentColor"/></g>`,
    cloud: `<g class="sw-cloud"><path d="${CLOUD_D}" fill="currentColor"/></g>`,
    cloudSmall: `<g class="sw-cloud"><path d="${CLOUD_SM_D}" fill="currentColor"/></g>`,
    // New.
    wisp: `<g class="sw-cloud"><path d="${WISP_D}" fill="currentColor"/></g>`,
    cloudHigh: `<g class="sw-cloud"><path d="${CLOUD_D}" transform="translate(4 -3) scale(0.75)" fill="currentColor"/></g>`,
    // A small sun / moon peeking out from behind the top-right of the cloud.
    sunPeek: `<g class="sw-sun"><circle cx="16" cy="7.5" r="3" fill="currentColor"/><g ${LINE} stroke-width="1.3">${rays(16, 7.5, 4.3, 5.6)}</g></g>`,
    moonPeek: `<g class="sw-moon"><path d="${MOON_D}" transform="translate(10.6 0.6) scale(0.5)" fill="currentColor"/></g>`,
    bolt: `<path class="sw-bolt" d="M13 16l-2 3h4l-2 3" fill="none" stroke="#fbbf24" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>`,
  };

  // Precipitation below the cloud (the cloud's lower edge is y≈20).
  const rain = (pts, w = 2) => `<g ${LINE} stroke-width="${w}" class="sw-rain">${lines(pts)}</g>`;
  const snow = (pts, r = 1) => `<g class="sw-snow" fill="currentColor">${dots(pts, r)}</g>`;
  const pellet = (pts, r = 0.6) => dots(pts, r).replace(/<circle /g, '<circle fill="currentColor" stroke="none" ');
  const PRECIP = {
    drizzle: rain([[7, 19.5, 7, 20.8], [10.3, 21.8, 10.3, 23.1], [13.7, 19.5, 13.7, 20.8], [17, 21.8, 17, 23.1]], 1.6),
    "light-rain": rain([[10, 19, 10, 22], [14, 21, 14, 24]]),
    rain: rain([[9, 19, 9, 22], [12, 21, 12, 24], [15, 19, 15, 22]]),
    "heavy-rain": rain([[6, 19, 6, 23], [9, 21, 9, 24.5], [12, 19, 12, 23], [15, 21, 15, 24.5], [18, 19, 18, 23]], 1.8),
    precipitation: `<g class="sw-drops" fill="currentColor">${drop(8, 21)}${drop(12, 22.8)}${drop(16, 21)}</g>`,
    flurries: snow([[10, 20.5], [14.5, 22.3]], 0.8),
    "light-snow": snow([[9.5, 20], [14.5, 22]]),
    snow: snow([[9, 20], [12, 22], [15, 20]]),
    "heavy-snow": snow([[7, 20], [10, 22.5], [13, 20], [16, 22.5], [19, 20]]),
    "very-light-sleet": `<g ${LINE} stroke-width="1.5" class="sw-rain"><line x1="10" y1="19" x2="10" y2="21.5"/>${pellet([[14, 22]], 0.55)}</g>`,
    "light-sleet": `<g ${LINE} stroke-width="2" class="sw-rain"><line x1="10" y1="19" x2="10" y2="22"/>${pellet([[14, 22]], 0.7)}</g>`,
    // The original sleet icon.
    sleet: `<g ${LINE} stroke-width="2" class="sw-rain"><line x1="9" y1="19" x2="9" y2="22"/><circle cx="12" cy="22" r="0.6" fill="currentColor" stroke="none"/><line x1="15" y1="19" x2="15" y2="22"/></g>`,
    "heavy-sleet": `<g ${LINE} stroke-width="1.8" class="sw-rain"><line x1="6" y1="19" x2="6" y2="22.5"/>${pellet([[9, 22.5], [15, 22.5]], 0.7)}<line x1="12" y1="19" x2="12" y2="22.5"/><line x1="18" y1="19" x2="18" y2="22.5"/></g>`,
    mixed: rain([[8, 19, 8, 22], [16, 19, 16, 22]]) + snow([[12, 21.5]]),
    hail: `<g class="sw-hail" fill="currentColor">${diamond(8.5, 21.6, 1.3)}${diamond(12, 23.2, 1.3)}${diamond(15.5, 21.6, 1.3)}</g>`,
  };

  const WIND_D = "M9.59 4.59A2 2 0 1 1 11 8H2m10.59 11.41A2 2 0 1 0 14 16H2m15.73-8.27A2.5 2.5 0 1 1 19.5 12H2";

  // ── Icons (canonical names) ─────────────────────────────────────────
  const ICONS = {
    "clear-day": P.sun,
    "clear-night": P.moon,
    "mostly-clear-day": P.sunSmall + P.wisp,
    "mostly-clear-night": P.moonSmall + P.wisp,
    "partly-cloudy-day": P.sunSmall + P.cloudSmall,
    "partly-cloudy-night": P.moonSmall + P.cloudSmall,
    "mostly-cloudy-day": P.sunPeek + P.cloud,
    "mostly-cloudy-night": P.moonPeek + P.cloud,
    cloudy: P.cloud,
    fog: `<g class="sw-cloud" ${LINE} stroke-width="2">${lines([[3, 6, 21, 6], [3, 10, 21, 10], [3, 14, 21, 14], [3, 18, 21, 18]])}</g>`,
    mist: `<g class="sw-cloud" ${LINE} stroke-width="2" stroke-dasharray="3 2.5">${lines([[3, 8, 21, 8], [5, 12, 21, 12], [3, 16, 19, 16]])}</g>`,
    haze: `<circle cx="12" cy="11" r="3.5" fill="currentColor"/><g ${LINE} stroke-width="1.6">${rays(12, 11, 5, 6.8, 5, 180, 360)}</g><g class="sw-cloud" ${LINE} stroke-width="2">${lines([[3, 17, 21, 17], [6, 20.5, 18, 20.5]])}</g>`,
    smoke: `<g class="sw-smoke" ${LINE} stroke-width="1.8"><path d="M7 21c-1.5-1.5 1.5-3 0-4.5s1.5-3 0-4.5"/><path d="M12 21c-1.5-1.5 1.5-3 0-4.5s1.5-3 0-4.5s1.5-3 0-4.5"/><path d="M17 21c-1.5-1.5 1.5-3 0-4.5s1.5-3 0-4.5"/></g>`,
    wind: `<g class="sw-wind" ${LINE} stroke-width="2"><path d="${WIND_D}"/></g>`,
    breezy: `<g class="sw-wind" ${LINE} stroke-width="1.8"><path d="M2 9h11a2.5 2.5 0 1 0-2.5-2.5M2 15h15a2.5 2.5 0 1 1-2.5 2.5"/></g>`,
    "dangerous-wind": `<g class="sw-wind" ${LINE} stroke-width="2"><path d="${WIND_D}"/></g><g ${LINE} stroke-width="1.4"><path d="M20.5 15.5L24 22H17Z"/><line x1="20.5" y1="17.6" x2="20.5" y2="19.3"/></g><circle cx="20.5" cy="20.6" r="0.7" fill="currentColor"/>`,
    "windy-variant": P.cloudHigh + `<g class="sw-wind" ${LINE} stroke-width="2"><path d="M2 18h12a2.5 2.5 0 1 0-2.5-2.5M2 21.5h16"/></g>`,
    tornado: `<g class="sw-tornado" ${LINE} stroke-width="2"><path d="M2 4h20M4.5 8h15M7 12h10M9.5 16h5.5M11 20h2.5"/></g>`,
    lightning: P.cloud + P.bolt,
    thunderstorm: P.cloud + P.bolt + rain([[7, 19, 7, 22], [17, 19, 17, 22]]),
    exceptional: `<g ${LINE} stroke-width="2"><path d="M12 3L22 20H2Z"/><line x1="12" y1="9" x2="12" y2="13.5"/></g><circle cx="12" cy="16.8" r="1.1" fill="currentColor"/>`,
  };
  for (const [name, layer] of Object.entries(PRECIP)) ICONS[name] = P.cloud + layer;

  // "Possible" precipitation: the light version, with the sun or moon out.
  const POSSIBLE = {
    rain: PRECIP["light-rain"],
    snow: PRECIP["light-snow"],
    sleet: PRECIP["light-sleet"],
    precipitation: PRECIP.precipitation,
    thunderstorm: P.bolt + rain([[7, 19, 7, 22], [17, 19, 17, 22]]),
  };
  for (const [kind, layer] of Object.entries(POSSIBLE)) {
    ICONS[`possible-${kind}-day`] = P.sunPeek + P.cloud + layer;
    ICONS[`possible-${kind}-night`] = P.moonPeek + P.cloud + layer;
  }

  // ── Names -> canonical icon ─────────────────────────────────────────
  const ALIASES = {
    // Home Assistant conditions
    sunny: "clear-day",
    clear: "clear-day",
    partlycloudy: "partly-cloudy-day",
    rainy: "rain",
    pouring: "heavy-rain",
    snowy: "snow",
    "snowy-rainy": "sleet",
    windy: "wind",
    "lightning-rainy": "thunderstorm",
    // Pirate Weather standard set
    none: "exceptional",
    // Keyword fallbacks' targets are canonical names already.
  };
  const NIGHT_OF = {
    "clear-day": "clear-night",
    "mostly-clear-day": "mostly-clear-night",
    "partly-cloudy-day": "partly-cloudy-night",
    "mostly-cloudy-day": "mostly-cloudy-night",
    haze: "mist", // haze is drawn with a sun
  };
  for (const kind of Object.keys(POSSIBLE)) NIGHT_OF[`possible-${kind}-day`] = `possible-${kind}-night`;

  const KEYWORDS = [
    [/tornado|funnel/, "tornado"],
    [/thunder|lightning|storm/, "thunderstorm"],
    [/hail/, "hail"],
    [/sleet|freezing|ice|mixed/, "sleet"],
    [/flurr/, "flurries"],
    [/snow/, "snow"],
    [/drizzle/, "drizzle"],
    [/heavy.*rain|pour|downpour/, "heavy-rain"],
    [/rain|shower/, "rain"],
    [/precip/, "precipitation"],
    [/smoke|fire/, "smoke"],
    [/haze|dust|sand/, "haze"],
    [/mist/, "mist"],
    [/fog/, "fog"],
    [/danger|gale/, "dangerous-wind"],
    [/breez/, "breezy"],
    [/wind|gust/, "wind"],
    [/overcast|cloud/, "cloudy"],
    [/clear|sun|fair/, "clear-day"],
  ];

  function resolve(name, opts = {}) {
    let key = String(name == null ? "" : name).trim().toLowerCase();
    key = ALIASES[key] || key;
    if (!ICONS[key]) {
      const possible = key.match(/^(?:possible|chance)[-_ ](.+?)(?:[-_ ](day|night))?$/);
      if (possible) {
        const found = KEYWORDS.find(([re]) => re.test(possible[1]));
        let kind = found ? found[1] : "precipitation";
        kind = { "heavy-rain": "rain", drizzle: "rain", flurries: "snow", hail: "sleet" }[kind] || kind;
        if (!POSSIBLE[kind]) kind = "precipitation";
        key = `possible-${kind}-${possible[2] || "day"}`;
      } else {
        const found = KEYWORDS.find(([re]) => re.test(key));
        key = found ? found[1] : "cloudy";
      }
    }
    if (opts.night && NIGHT_OF[key]) key = NIGHT_OF[key];
    return key;
  }

  function svg(name, opts = {}) {
    const key = resolve(name, opts);
    const cls = opts.className ? ` ${opts.className}` : "";
    return `<svg viewBox="0 0 24 24" class="wx-svg${cls}" data-icon="${key}" aria-hidden="true">${ICONS[key]}</svg>`;
  }

  // Short tags for the "broadcast" weather style.
  const TAGS = {
    "clear-day": "CLEAR", "clear-night": "CLEAR",
    "mostly-clear-day": "M.CLEAR", "mostly-clear-night": "M.CLEAR",
    "partly-cloudy-day": "P.CLOUDY", "partly-cloudy-night": "P.CLOUDY",
    "mostly-cloudy-day": "M.CLOUDY", "mostly-cloudy-night": "M.CLOUDY",
    cloudy: "CLOUDY", fog: "FOG", mist: "MIST", haze: "HAZE", smoke: "SMOKE",
    drizzle: "DRIZZLE", "light-rain": "LT.RAIN", rain: "RAIN", "heavy-rain": "HVY.RAIN", precipitation: "PRECIP",
    flurries: "FLURRIES", "light-snow": "LT.SNOW", snow: "SNOW", "heavy-snow": "HVY.SNOW",
    "very-light-sleet": "ICY", "light-sleet": "ICY", sleet: "ICY", "heavy-sleet": "ICY", mixed: "MIXED", hail: "HAIL",
    lightning: "LIGHTNING", thunderstorm: "STORMS",
    wind: "WINDY", breezy: "BREEZY", "dangerous-wind": "HIGH WIND", "windy-variant": "WINDY", tornado: "TORNADO",
    exceptional: "ALERT",
  };
  for (const kind of Object.keys(POSSIBLE)) {
    const tag = { rain: "CHC.RAIN", snow: "CHC.SNOW", sleet: "CHC.ICE", precipitation: "CHC.PRECIP", thunderstorm: "CHC.STORM" }[kind];
    TAGS[`possible-${kind}-day`] = TAGS[`possible-${kind}-night`] = tag;
  }
  const label = (name, opts) => TAGS[resolve(name, opts)] || "WEATHER";

  // Animation classes used by the icons. Scoped to the sw-* classes only, so
  // the page can include it without touching anything else.
  const CSS = `
.sw-sun,.sw-moon{transform-box:fill-box;transform-origin:center}
.sw-sun{animation:sw-spin 12s linear infinite}
.sw-moon{animation:sw-rock 4s ease-in-out infinite}
.sw-cloud{animation:sw-drift 6s ease-in-out infinite alternate}
.sw-wind{animation:sw-drift 4s ease-in-out infinite alternate}
.sw-rain line{animation:sw-fall 1s linear infinite}
.sw-snow circle{animation:sw-snow-fall 2.5s linear infinite}
.sw-drops path{animation:sw-fall 1.3s linear infinite}
.sw-hail path{animation:sw-hail 1.1s ease-in infinite}
.sw-bolt{animation:sw-flash 3s step-end infinite}
.sw-smoke path{animation:sw-rise 3.2s ease-in-out infinite}
.sw-tornado{transform-box:fill-box;transform-origin:50% 100%;animation:sw-sway 2.4s ease-in-out infinite alternate}
@keyframes sw-spin{from{transform:rotate(0deg)}to{transform:rotate(360deg)}}
@keyframes sw-rock{0%,100%{transform:rotate(-8deg)}50%{transform:rotate(8deg)}}
@keyframes sw-drift{from{transform:translateX(-1.5px)}to{transform:translateX(1.5px)}}
@keyframes sw-fall{0%{transform:translateY(-4px);opacity:0}30%{opacity:1}100%{transform:translateY(6px);opacity:0}}
@keyframes sw-snow-fall{0%{transform:translateY(-4px) translateX(0);opacity:0}20%{opacity:1}100%{transform:translateY(8px) translateX(2px);opacity:0}}
@keyframes sw-hail{0%{transform:translateY(-4px);opacity:0}25%{opacity:1}75%{transform:translateY(3px)}85%{transform:translateY(2px)}100%{transform:translateY(3px);opacity:0}}
@keyframes sw-flash{0%,92%{opacity:0}93%{opacity:1}95%{opacity:0}97%{opacity:1}99%{opacity:0}}
@keyframes sw-rise{0%{transform:translateY(1.5px);opacity:.35}50%{opacity:1}100%{transform:translateY(-1.5px);opacity:.35}}
@keyframes sw-sway{from{transform:rotate(-4deg)}to{transform:rotate(4deg)}}
@media (prefers-reduced-motion:reduce){[class*="sw-"],[class*="sw-"] *{animation:none!important}}
`;

  root.RundownWxIcons = {
    version: VERSION,
    icons: Object.keys(ICONS),
    resolve,
    svg,
    label,
    CSS,
  };
})(globalThis);
