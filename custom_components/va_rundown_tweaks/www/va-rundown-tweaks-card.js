// View Assist Rundown Tweaks — Lovelace card that hosts the Rundown page.
//
// The page is served same-origin from /va_rundown_tweaks/static and, being
// same-origin, reads the signed-in user's `hass` object from this window
// instead of needing a long-lived token.
//
// Options:
//   fullscreen: true   cover the whole browser window (used by the View
//                      Assist "rundowntweaks" view), regardless of the dashboard's
//                      header/sidebar or View Assist screen mode
//   height: <css>      card height when not full screen (default 100vh)
const VA_RUNDOWN_VERSION = new URL(import.meta.url).searchParams.get("v") || "0";

class VaRundownCard extends HTMLElement {
  setConfig(config) {
    this._config = { height: "100vh", fullscreen: false, ...config };
    this._render();
  }

  // The page reads hass from the parent window itself; nothing to forward.
  set hass(_hass) {}

  getCardSize() {
    return 12;
  }

  getGridOptions() {
    return { columns: "full", rows: 8, min_rows: 4 };
  }

  _render() {
    if (!this.shadowRoot) this.attachShadow({ mode: "open" });
    const { height, fullscreen } = this._config;
    const key = `${height}|${fullscreen}`;
    if (this._frame && this._frame.dataset.key === key) return;
    const src = `/va_rundown_tweaks/static/rundown.html?v=${encodeURIComponent(VA_RUNDOWN_VERSION)}`;
    // Full screen: fixed to the viewport above Home Assistant's header and
    // sidebar (z-index 10, same as the panel's ?kiosk mode), so the view is
    // edge to edge on any device whatever its View Assist screen mode.
    const frameCss = fullscreen
      ? "position: fixed; inset: 0; width: 100vw; height: 100dvh; z-index: 10;"
      : `width: 100%; height: ${height};`;
    this.shadowRoot.innerHTML = `
      <style>
        :host { display: block; ${fullscreen ? "height: 100dvh;" : ""} }
        iframe { display: block; border: 0; background: #080909; ${frameCss} }
      </style>
      <iframe title="Rundown" allow="fullscreen" src="${src}"></iframe>`;
    this._frame = this.shadowRoot.querySelector("iframe");
    this._frame.dataset.key = key;
  }
}

if (!customElements.get("va-rundown-tweaks-card")) {
  customElements.define("va-rundown-tweaks-card", VaRundownCard);
  window.customCards = window.customCards || [];
  window.customCards.push({
    type: "va-rundown-tweaks-card",
    name: "Rundown Tweaks",
    description: "The View Assist Rundown Tweaks dashboard (configure under Settings → Devices & services).",
  });
}
