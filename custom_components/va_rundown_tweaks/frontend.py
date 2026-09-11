"""Frontend wiring: static files, Lovelace resources and the sidebar panel."""

from __future__ import annotations

from collections.abc import Mapping
import logging
from typing import Any

from homeassistant.components import frontend, panel_custom
from homeassistant.components.lovelace import MODE_STORAGE
from homeassistant.core import HomeAssistant

from .const import (
    CONF_LOAD_FONTS,
    CONF_PANEL_ICON,
    CONF_PANEL_TITLE,
    CONF_REGISTER_PANEL,
    FRONTEND_VERSION,
    LOVELACE_MODULES,
    PANEL_COMPONENT,
    PANEL_URL_PATH,
    STATIC_URL,
)
from .rundown_config import merged_options

_LOGGER = logging.getLogger(__name__)

FONTS_CSS_URL = (
    "https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@300;400;500;600"
    "&family=IBM+Plex+Sans:wght@300;400;500;600;700&display=swap"
)
FONTS_PREFIX = "https://fonts.googleapis.com/css2?family=IBM+Plex"
PAGE_URL = f"{STATIC_URL}/rundown.html?v={FRONTEND_VERSION}"


def _storage_resources(hass: HomeAssistant):
    """Return the Lovelace resource collection, or None in YAML mode."""
    lovelace = hass.data.get("lovelace")
    if lovelace is None:
        return None
    # Renamed from `mode` to `resource_mode` in 2026.2.
    mode = getattr(lovelace, "resource_mode", None) or getattr(lovelace, "mode", None)
    if mode != MODE_STORAGE:
        _LOGGER.info(
            "Lovelace resources are in YAML mode; add %s modules manually", STATIC_URL
        )
        return None
    return lovelace.resources


async def async_sync_lovelace_resources(
    hass: HomeAssistant, options: Mapping[str, Any]
) -> None:
    """Create, version-bump or remove the resources this integration owns."""
    if (resources := _storage_resources(hass)) is None:
        return
    await resources.async_get_info()  # ensures the collection is loaded
    opts = merged_options(options)

    wanted = {
        f"{STATIC_URL}/{name}": f"{STATIC_URL}/{name}?v={FRONTEND_VERSION}"
        for name in LOVELACE_MODULES
    }
    for item in list(resources.async_items()):
        url = str(item["url"])
        base = url.split("?")[0]
        if not base.startswith(f"{STATIC_URL}/"):
            continue
        if base not in wanted:
            await resources.async_delete_item(item["id"])
        elif url != wanted[base]:
            await resources.async_update_item(
                item["id"], {"res_type": "module", "url": wanted[base]}
            )
        wanted.pop(base, None)
    for url in wanted.values():
        await resources.async_create_item({"res_type": "module", "url": url})

    font_items = [
        item for item in resources.async_items() if str(item["url"]).startswith(FONTS_PREFIX)
    ]
    if opts[CONF_LOAD_FONTS] and not font_items:
        await resources.async_create_item({"res_type": "css", "url": FONTS_CSS_URL})
    elif not opts[CONF_LOAD_FONTS]:
        # Only remove the exact stylesheet this integration adds; a user's
        # own IBM Plex resource is left alone.
        for item in font_items:
            if item["url"] == FONTS_CSS_URL:
                await resources.async_delete_item(item["id"])


async def async_remove_lovelace_resources(hass: HomeAssistant) -> None:
    """Remove every resource this integration created."""
    if (resources := _storage_resources(hass)) is None:
        return
    await resources.async_get_info()
    for item in list(resources.async_items()):
        url = str(item["url"])
        if url.startswith(f"{STATIC_URL}/") or url == FONTS_CSS_URL:
            await resources.async_delete_item(item["id"])


async def async_sync_panel(hass: HomeAssistant, options: Mapping[str, Any]) -> None:
    """Register (or re-register with new title/icon) or remove the panel."""
    opts = merged_options(options)
    async_remove_panel(hass)
    if not opts[CONF_REGISTER_PANEL]:
        return
    await panel_custom.async_register_panel(
        hass,
        frontend_url_path=PANEL_URL_PATH,
        webcomponent_name=PANEL_COMPONENT,
        module_url=f"{STATIC_URL}/va-rundown-tweaks-panel.js?v={FRONTEND_VERSION}",
        sidebar_title=opts[CONF_PANEL_TITLE],
        sidebar_icon=opts[CONF_PANEL_ICON],
        require_admin=False,
        config={"page_url": PAGE_URL},
    )


def async_remove_panel(hass: HomeAssistant) -> None:
    """Remove the sidebar panel if registered."""
    frontend.async_remove_panel(hass, PANEL_URL_PATH, warn_if_unknown=False)
