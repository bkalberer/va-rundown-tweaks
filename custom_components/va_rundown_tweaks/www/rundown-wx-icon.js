// <rundown-tweaks-wx-icon condition="fog" night="false">
//
// Animated weather icon for the View Assist Rundown Tweaks clock view. Draws
// from the shared icon set in rundown-wx-icons.js — the same icons the
// Rundown page uses — and accepts any Home Assistant weather condition or
// Pirate Weather icon name. `night="true"` swaps day icons for their night
// versions (sun -> moon).
//
// Named rundown-tweaks-wx-icon (not rundown-wx-icon) so it can't collide
// with a standalone Rundown setup's element of that name: a browser keeps
// whichever definition of a custom element name loads first.
import "./rundown-wx-icons.js";

const HOST_CSS =
  ":host{display:inline-block;line-height:1}" +
  "svg{width:1em;height:1em;fill:none;stroke:none;overflow:visible;display:block}";

class RundownTweaksWxIcon extends HTMLElement {
  static get observedAttributes() {
    return ["condition", "night"];
  }

  connectedCallback() {
    this._render();
  }

  attributeChangedCallback(name, oldVal, newVal) {
    if (oldVal !== newVal) this._render();
  }

  _render() {
    if (!this.shadowRoot) this.attachShadow({ mode: "open" });
    const icons = globalThis.RundownWxIcons;
    const markup =
      `<style>${HOST_CSS}${icons.CSS}</style>` +
      icons.svg(this.getAttribute("condition") || "sunny", {
        night: this.getAttribute("night") === "true",
      });
    if (this._last === markup) return;
    this._last = markup;
    this.shadowRoot.innerHTML = markup;
  }
}

if (!customElements.get("rundown-tweaks-wx-icon")) {
  customElements.define("rundown-tweaks-wx-icon", RundownTweaksWxIcon);
}
