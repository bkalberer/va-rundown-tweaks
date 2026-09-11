// View Assist Rundown Tweaks — sidebar panel.
//
// Open /va-rundown-tweaks for the panel inside the normal Home Assistant chrome, or
// /va-rundown-tweaks?kiosk to have the page cover the whole window (for wall
// displays and View Assist devices without their own kiosk mode).
class VaRundownPanel extends HTMLElement {
  set panel(panel) {
    this._panel = panel;
    this._render();
  }

  set hass(_hass) {}

  set narrow(_narrow) {}

  _render() {
    if (this._frame || !this._panel) return;
    const src = (this._panel.config && this._panel.config.page_url) || "/va_rundown_tweaks/static/rundown.html";
    const kiosk = new URLSearchParams(window.location.search).has("kiosk");
    this.attachShadow({ mode: "open" });
    this.shadowRoot.innerHTML = `
      <style>
        :host { display: block; height: 100%; background: #080909; }
        iframe { display: block; border: 0; width: 100%; height: 100dvh; background: #080909; }
        iframe.kiosk { position: fixed; inset: 0; width: 100vw; height: 100dvh; z-index: 10; }
      </style>
      <iframe title="Rundown" allow="fullscreen" class="${kiosk ? "kiosk" : ""}" src="${src}"></iframe>`;
    this._frame = this.shadowRoot.querySelector("iframe");
  }
}

if (!customElements.get("va-rundown-tweaks-panel")) {
  customElements.define("va-rundown-tweaks-panel", VaRundownPanel);
}
