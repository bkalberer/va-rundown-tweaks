class ViewAssistMenuCard extends HTMLElement {
  static getConfigElement() {
    return document.createElement("hui-error-card");
  }

  static getStubConfig() {
    return {
      position: "right",
      reverse: true,
    };
  }

  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._config = {};
    this._hass = undefined;
    this._signature = "";
  }

  setConfig(config) {
    this._config = {
      position: "right",
      reverse: true,
      width: "clamp(56px, 7vw, 90px)",
      padding: "0.5vw",
      gap: "0px",
      ...config,
    };
    this._signature = "";
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  getCardSize() {
    return 1;
  }

  _getViewAssistEntity() {
    return (
      this._config.entity || localStorage.getItem("view_assist_sensor") || ""
    );
  }

  _getSignature(entityId, menuItems) {
    const entityStates = menuItems
      .filter((item) => typeof item === "string" && item.startsWith("entity:"))
      .map((item) => {
        const target = item.split("|")[0].slice(7);
        return `${target}:${this._hass?.states[target]?.state || ""}`;
      });

    return JSON.stringify({
      entityId,
      menuItems,
      entityStates,
      mode: this._hass?.states[entityId]?.attributes?.mode || "",
      path: window.location.pathname,
      config: this._config,
    });
  }

  _normalisePath(path) {
    return path.replace(/\/{2,}/g, "/");
  }

  _getMenuItems(entityId) {
    const items = this._hass?.states[entityId]?.attributes?.menu_items;
    if (!Array.isArray(items)) {
      return [];
    }

    const filtered = items.filter(
      (item) => typeof item === "string" && item !== "menu",
    );
    return this._config.reverse ? [...filtered].reverse() : filtered;
  }

  _parseItem(entityId, item) {
    const entity = this._hass.states[entityId];
    const dashboard = (entity?.attributes?.dashboard || "/view-assist").replace(
      /\/$/,
      "",
    );
    const predefined = {
      home: {
        type: "view",
        target: entity?.attributes?.home_screen || `${dashboard}/clock`,
        icon: "home",
      },
      weather: {
        type: "view",
        target: `${dashboard}/weather`,
        icon: "weather-sunny",
      },
      camera: {
        type: "view",
        target: `${dashboard}/camera`,
        icon: "cctv",
      },
      music: {
        type: "view",
        target: `${dashboard}/music`,
        icon: "music",
      },
    };

    if (!item.includes(":")) {
      return predefined[item] || {
        type: "invalid",
        target: item,
        icon: "alert-circle-outline",
      };
    }

    const [definition, iconDefinition = "help-circle"] = item.split("|");
    const separator = definition.indexOf(":");
    const type = definition.slice(0, separator);
    let target = definition.slice(separator + 1);
    const icons = iconDefinition.split(",").map((icon) => icon.trim());

    if (type === "view" && !target.startsWith("/")) {
      target = `${dashboard}/${target}`;
    }

    return {
      type,
      target: type === "view" ? this._normalisePath(target) : target,
      icon: icons[0] || "help-circle",
      offIcon: icons[1],
    };
  }

  _createButton(entityId, item) {
    const parsed = this._parseItem(entityId, item);
    const button = document.createElement("button");
    button.type = "button";
    button.className = "menu-button";
    button.title = item;

    let iconName = parsed.icon;
    if (parsed.type === "entity") {
      const state = this._hass.states[parsed.target]?.state;
      if (state === "off" && parsed.offIcon) {
        iconName = parsed.offIcon;
      }
      button.classList.toggle("on", state === "on");
    }

    if (
      parsed.type === "view" &&
      window.location.pathname === parsed.target
    ) {
      button.classList.add("selected");
    }

    const icon = document.createElement("ha-icon");
    icon.setAttribute("icon", `mdi:${iconName}`);
    button.append(icon);

    button.addEventListener("click", () => {
      this._handleTap(entityId, parsed);
    });

    if (parsed.type === "entity" || parsed.type === "press") {
      button.addEventListener("contextmenu", (event) => {
        event.preventDefault();
        const moreInfo = new Event("hass-more-info", {
          bubbles: true,
          composed: true,
        });
        moreInfo.detail = { entityId: parsed.target };
        this.dispatchEvent(moreInfo);
      });
    }

    return button;
  }

  _handleTap(entityId, item) {
    if (!this._hass) {
      return;
    }

    if (item.type === "view") {
      this._hass.callService("view_assist", "navigate", {
        device: entityId,
        path: item.target,
      });
      return;
    }

    if (item.type === "entity") {
      const domain = item.target.split(".")[0];
      this._hass.callService(domain, "toggle", {
        entity_id: item.target,
      });
      return;
    }

    // "press:<entity_id>|<icon>" — fires a stateless action on a single
    // entity. Unlike "entity:", this calls <domain>.press rather than
    // <domain>.toggle, which is what button entities (button.press) need
    // since the button domain has no toggle service. Unlike "service:",
    // it carries an entity_id, so it can target one specific device.
    if (item.type === "press") {
      const domain = item.target.split(".")[0];
      this._hass.callService(domain, "press", {
        entity_id: item.target,
      });
      return;
    }

    if (item.type === "service") {
      const separator = item.target.indexOf(".");
      if (separator > 0) {
        this._hass.callService(
          item.target.slice(0, separator),
          item.target.slice(separator + 1),
          {},
        );
      }
    }
  }

  _render() {
    if (!this.shadowRoot || !this._hass) {
      return;
    }

    const entityId = this._getViewAssistEntity();
    const menuItems = this._getMenuItems(entityId);
    const signature = this._getSignature(entityId, menuItems);
    if (signature === this._signature) {
      return;
    }
    this._signature = signature;

    this.shadowRoot.replaceChildren();

    const style = document.createElement("style");
    const position = this._config.position === "left" ? "left" : "right";
    // Night mode: dim the whole menu and switch icons to the same red the
    // clock view uses, so the menu doesn't glare next to dimmed content.
    const isNight =
      this._hass?.states[entityId]?.attributes?.mode === "night";
    const nightOpacity = this._config.night_opacity || "0.35";
    const nightColor = this._config.night_color || "red";
    style.textContent = `
      :host {
        display: block;
      }

      ha-card {
        position: fixed;
        ${position}: ${this._config.offset || "1.5vw"};
        top: 50%;
        transform: translateY(-50%);
        z-index: ${this._config.z_index || 10};
        width: ${this._config.width};
        padding: ${this._config.padding};
        box-sizing: border-box;
        border: none;
        border-radius: ${this._config.border_radius || "18px"};
        background: ${
          this._config.background || "rgba(20, 20, 20, 0.92)"
        };
        box-shadow: ${
          this._config.box_shadow || "0 4px 18px rgba(0, 0, 0, 0.35)"
        };
        opacity: ${isNight ? nightOpacity : "1"};
        transition: opacity 0.6s ease;
      }

      .menu {
        display: grid;
        grid-template-columns: 1fr;
        gap: ${this._config.gap};
      }

      .menu-button {
        display: grid;
        place-items: center;
        width: 100%;
        aspect-ratio: 1 / 1;
        margin: 0;
        padding: 0;
        border: none;
        border-radius: var(--ha-card-border-radius, 12px);
        color: ${isNight ? nightColor : "white"};
        background: transparent;
        cursor: pointer;
      }

      .menu-button ha-icon {
        width: 90%;
        height: 90%;
        --mdc-icon-size: 90%;
      }

      .menu-button.on {
        color: ${isNight ? nightColor : "var(--warning-color)"};
      }

      .menu-button.selected {
        color: ${isNight ? nightColor : "var(--primary-color)"};
      }

      .menu-button:active {
        background: rgba(255, 255, 255, 0.12);
      }
    `;

    const card = document.createElement("ha-card");
    const menu = document.createElement("div");
    menu.className = "menu";

    for (const item of menuItems) {
      menu.append(this._createButton(entityId, item));
    }

    card.append(menu);
    this.shadowRoot.append(style, card);
  }
}

if (!customElements.get("view-assist-menu-card")) {
  customElements.define("view-assist-menu-card", ViewAssistMenuCard);
}

window.customCards = window.customCards || [];
window.customCards.push({
  type: "view-assist-menu-card",
  name: "View Assist Menu Card",
  description: "Reusable menu sourced from a View Assist device configuration.",
});