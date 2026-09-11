const WX_CSS = `<style>:host{display:inline-block;line-height:1}svg{width:1em;height:1em;fill:none;stroke:none;overflow:visible;display:block}.sw-sun{transform-origin:center;animation:sw-spin 12s linear infinite}.sw-moon{transform-origin:center;animation:sw-rock 4s ease-in-out infinite}.sw-cloud{animation:sw-drift 6s ease-in-out infinite alternate}.sw-rain line{animation:sw-fall 1s linear infinite}.sw-snow circle{animation:sw-snow-fall 2.5s linear infinite}.sw-bolt{animation:sw-flash 3s step-end infinite}.sw-wind{animation:sw-drift 4s ease-in-out infinite alternate}@keyframes sw-spin{from{transform:rotate(0deg)}to{transform:rotate(360deg)}}@keyframes sw-rock{0%,100%{transform:rotate(-8deg)}50%{transform:rotate(8deg)}}@keyframes sw-drift{from{transform:translateX(-1.5px)}to{transform:translateX(1.5px)}}@keyframes sw-fall{0%{transform:translateY(-4px);opacity:0}30%{opacity:1}100%{transform:translateY(6px);opacity:0}}@keyframes sw-snow-fall{0%{transform:translateY(-4px) translateX(0);opacity:0}20%{opacity:1}100%{transform:translateY(8px) translateX(2px);opacity:0}}@keyframes sw-flash{0%,92%{opacity:0}93%{opacity:1}95%{opacity:0}97%{opacity:1}99%{opacity:0}}@media (prefers-reduced-motion:reduce){*{animation:none!important}}</style>`;

const CLOUD_D = "M18 10h-1.26A8 8 0 1 0 9 20h9a5 5 0 0 0 0-10z";
const CLOUD_SM_D = "M20 14h-1a4 4 0 1 0-7.73-1.47A5 5 0 0 0 12 22h8a4 4 0 0 0 0-8z";

const WX_IC = {
  sun: `<svg viewBox="0 0 24 24" class="sw-sun"><circle cx="12" cy="12" r="5" fill="currentColor"/><g stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="12" y1="1" x2="12" y2="4"/><line x1="12" y1="20" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="6.34" y2="6.34"/><line x1="17.66" y1="17.66" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="4" y2="12"/><line x1="20" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="6.34" y2="17.66"/><line x1="17.66" y1="6.34" x2="19.78" y2="4.22"/></g></svg>`,
  moon: `<svg viewBox="0 0 24 24" class="sw-moon"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" fill="currentColor"/></svg>`,
  pcd: `<svg viewBox="0 0 24 24"><g class="sw-sun"><circle cx="10" cy="10" r="4" fill="currentColor"/><g stroke="currentColor" stroke-width="1.5"><line x1="10" y1="3" x2="10" y2="5"/><line x1="10" y1="15" x2="10" y2="17"/><line x1="5" y1="5" x2="6.5" y2="6.5"/><line x1="13.5" y1="13.5" x2="15" y2="15"/><line x1="3" y1="10" x2="5" y2="10"/><line x1="15" y1="10" x2="17" y2="10"/><line x1="5" y1="15" x2="6.5" y2="13.5"/><line x1="13.5" y1="6.5" x2="15" y2="5"/></g></g><path class="sw-cloud" d="${CLOUD_SM_D}" fill="currentColor"/></svg>`,
  pcn: `<svg viewBox="0 0 24 24"><path class="sw-moon" d="M16 11.79A7 7 0 1 1 8.21 4 5 5 0 0 0 16 11.79z" fill="currentColor"/><path class="sw-cloud" d="${CLOUD_SM_D}" fill="currentColor"/></svg>`,
  cloudy: `<svg viewBox="0 0 24 24" class="sw-cloud"><path d="${CLOUD_D}" fill="currentColor"/></svg>`,
  rain: `<svg viewBox="0 0 24 24"><path class="sw-cloud" d="${CLOUD_D}" fill="currentColor"/><g stroke="currentColor" stroke-width="2" stroke-linecap="round" class="sw-rain"><line x1="9" y1="19" x2="9" y2="22"/><line x1="12" y1="21" x2="12" y2="24"/><line x1="15" y1="19" x2="15" y2="22"/></g></svg>`,
  sleet: `<svg viewBox="0 0 24 24"><path class="sw-cloud" d="${CLOUD_D}" fill="currentColor"/><g stroke="currentColor" stroke-width="2" stroke-linecap="round" class="sw-rain"><line x1="9" y1="19" x2="9" y2="22"/><circle cx="12" cy="22" r="0.6" fill="currentColor" stroke="none"/><line x1="15" y1="19" x2="15" y2="22"/></g></svg>`,
  snow: `<svg viewBox="0 0 24 24"><path class="sw-cloud" d="${CLOUD_D}" fill="currentColor"/><g class="sw-snow" fill="currentColor"><circle cx="9" cy="20" r="1"/><circle cx="12" cy="22" r="1"/><circle cx="15" cy="20" r="1"/></g></svg>`,
  wind: `<svg viewBox="0 0 24 24" class="sw-wind" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M9.59 4.59A2 2 0 1 1 11 8H2m10.59 11.41A2 2 0 1 0 14 16H2m15.73-8.27A2.5 2.5 0 1 1 19.5 12H2"/></svg>`,
  fog: `<svg viewBox="0 0 24 24" class="sw-cloud" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/><line x1="3" y1="14" x2="21" y2="14"/><line x1="3" y1="18" x2="21" y2="18"/></svg>`,
  storm: `<svg viewBox="0 0 24 24"><path class="sw-cloud" d="${CLOUD_D}" fill="currentColor"/><path class="sw-bolt" d="M13 16l-2 3h4l-2 3" fill="none" stroke="#fbbf24" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>`
};

function pickIcon(condition, isNight) {
  switch (condition) {
    case "clear-night": return WX_IC.moon;
    case "sunny":
    case "clear": return isNight ? WX_IC.moon : WX_IC.sun;
    case "partlycloudy": return isNight ? WX_IC.pcn : WX_IC.pcd;
    case "rainy":
    case "pouring": return WX_IC.rain;
    case "hail":
    case "snowy-rainy": return WX_IC.sleet;
    case "snowy": return WX_IC.snow;
    case "windy":
    case "windy-variant": return WX_IC.wind;
    case "fog": return WX_IC.fog;
    case "lightning":
    case "lightning-rainy": return WX_IC.storm;
    default: return WX_IC.cloudy;
  }
}

class RundownWxIcon extends HTMLElement {
  static get observedAttributes() { return ["condition", "night"]; }

  connectedCallback() { this._render(); }

  attributeChangedCallback(name, oldVal, newVal) {
    if (oldVal !== newVal) this._render();
  }

  _render() {
    if (!this.shadowRoot) this.attachShadow({ mode: "open" });
    const condition = this.getAttribute("condition") || "sunny";
    const isNight = this.getAttribute("night") === "true";
    const markup = WX_CSS + pickIcon(condition, isNight);
    if (this._last === markup) return;
    this._last = markup;
    this.shadowRoot.innerHTML = markup;
  }
}

if (!customElements.get("rundown-wx-icon")) {
  customElements.define("rundown-wx-icon", RundownWxIcon);
}