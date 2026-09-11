"""Diagnostics for View Assist Rundown Tweaks."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_GRAPH_URL, CONF_MS_CLIENT_ID, CONF_TICKER_CUSTOM_URL, SECRET_KEYS
from .websocket import async_page_config

REDACT = SECRET_KEYS | {CONF_MS_CLIENT_ID, CONF_GRAPH_URL, CONF_TICKER_CUSTOM_URL}
REDACT_PAGE = {
    "weatherKey",
    "wmataKey",
    "icsUrl",
    "outlookUrl",
    "outlookToken",
    "esvKey",
    "lfmKey",
    "todoClientId",
    "todoClientSecret",
    "todoRefreshToken",
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return redacted options and the resulting page config."""
    page = await async_page_config(hass, entry, is_admin=False)
    page["bgImages"] = f"{len(page['bgImages'])} image(s)"
    return {
        "options": async_redact_data(dict(entry.options), REDACT),
        "page_config": async_redact_data(page, REDACT_PAGE),
    }
