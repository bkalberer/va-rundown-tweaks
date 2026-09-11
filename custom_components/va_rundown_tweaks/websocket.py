"""Websocket API used by the Rundown page."""

from __future__ import annotations

import asyncio
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    BUILTIN_FEEDS,
    CONF_BG_FOLDER,
    CONF_MS_REFRESH_TOKEN,
    CONF_TODO_SOURCE,
    DOMAIN,
    FETCH_MAX_BYTES,
    FETCH_TIMEOUT,
    WS_CONFIG,
    WS_FETCH,
    WS_SAVE_LAYOUT,
    WS_SAVE_TODO_TOKEN,
    WS_STATUS,
)
from .http import list_photos, resolve_photo_folder
from .rundown_config import (
    build_page_config,
    fetch_url_for_source,
    options_from_page_layout,
    photo_urls,
)

FETCH_SOURCES = ["ics", "custom", *BUILTIN_FEEDS]


@callback
def async_register_websocket_commands(hass: HomeAssistant) -> None:
    """Register the integration's websocket commands."""
    websocket_api.async_register_command(hass, ws_status)
    websocket_api.async_register_command(hass, ws_get_config)
    websocket_api.async_register_command(hass, ws_save_layout)
    websocket_api.async_register_command(hass, ws_save_todo_token)
    websocket_api.async_register_command(hass, ws_fetch)


def _loaded_entry(hass: HomeAssistant) -> ConfigEntry | None:
    return next(
        (
            entry
            for entry in hass.config_entries.async_entries(DOMAIN)
            if entry.state is ConfigEntryState.LOADED
        ),
        None,
    )


def _not_loaded(connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    connection.send_error(msg["id"], "not_loaded", "View Assist Rundown Tweaks is not set up")


async def async_page_config(
    hass: HomeAssistant, entry: ConfigEntry, *, is_admin: bool
) -> dict[str, Any]:
    """Build the page config for an entry (shared with diagnostics)."""

    def _photos() -> list[str]:
        folder = resolve_photo_folder(hass, entry.options.get(CONF_BG_FOLDER))
        return photo_urls(entry.options, list_photos(folder))

    photos = await hass.async_add_executor_job(_photos)
    return build_page_config(
        entry.options,
        photos=photos,
        is_admin=is_admin,
        default_lat=hass.config.latitude,
        default_lon=hass.config.longitude,
    )


@websocket_api.websocket_command({vol.Required("type"): WS_STATUS})
@callback
def ws_status(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    """Tell open Rundown / sky pages whether the integration is running.

    Pages poll this so disabling the integration stops them within a minute.
    """
    connection.send_result(msg["id"], {"loaded": _loaded_entry(hass) is not None})


@websocket_api.websocket_command({vol.Required("type"): WS_CONFIG})
@websocket_api.async_response
async def ws_get_config(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    """Return the page config to any authenticated user.

    The page calls third-party APIs (Pirate Weather, WMATA, ESV, Last.fm,
    Microsoft Graph) straight from the browser, so those keys are sent to
    signed-in Home Assistant users. That replaces the previous setup, where
    the same keys sat in a JSON file anyone could read from /local.
    """
    if (entry := _loaded_entry(hass)) is None:
        _not_loaded(connection, msg)
        return
    connection.send_result(
        msg["id"], await async_page_config(hass, entry, is_admin=connection.user.is_admin)
    )


@websocket_api.websocket_command(
    {
        vol.Required("type"): WS_SAVE_LAYOUT,
        vol.Optional("layout"): dict,
        vol.Optional("hidden_widgets"): [str],
        vol.Optional("ticker_height"): vol.Any(None, vol.Coerce(int)),
        vol.Optional("wx_rotation_enabled"): bool,
        vol.Optional("wx_slides"): [dict],
    }
)
@websocket_api.require_admin
@websocket_api.async_response
async def ws_save_layout(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    """Persist the in-page layout / weather-rotation editors (admins only)."""
    if (entry := _loaded_entry(hass)) is None:
        _not_loaded(connection, msg)
        return
    updates = options_from_page_layout(msg)
    hass.config_entries.async_update_entry(entry, options={**entry.options, **updates})
    connection.send_result(msg["id"], {"saved": sorted(updates)})


@websocket_api.websocket_command(
    {
        vol.Required("type"): WS_SAVE_TODO_TOKEN,
        vol.Required("refresh_token"): vol.All(str, vol.Length(min=1, max=8192)),
    }
)
@websocket_api.async_response
async def ws_save_todo_token(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    """Store a rotated Microsoft To Do refresh token.

    Open to any signed-in user because the kiosk that refreshes the token is
    usually not an admin; it can only replace this one field, and only while
    the Microsoft task source is selected.
    """
    if (entry := _loaded_entry(hass)) is None:
        _not_loaded(connection, msg)
        return
    if entry.options.get(CONF_TODO_SOURCE) != "microsoft":
        connection.send_error(msg["id"], "not_allowed", "Microsoft To Do is not the task source")
        return
    if entry.options.get(CONF_MS_REFRESH_TOKEN) != msg["refresh_token"]:
        hass.config_entries.async_update_entry(
            entry, options={**entry.options, CONF_MS_REFRESH_TOKEN: msg["refresh_token"]}
        )
    connection.send_result(msg["id"], {"saved": True})


@websocket_api.websocket_command(
    {vol.Required("type"): WS_FETCH, vol.Required("source"): vol.In(FETCH_SOURCES)}
)
@websocket_api.async_response
async def ws_fetch(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    """Fetch the calendar or a ticker feed server-side.

    Accepts a source id rather than a URL, so it cannot be used as an open
    proxy and the private ICS link never has to reach the browser or a
    third-party CORS proxy.
    """
    if (entry := _loaded_entry(hass)) is None:
        _not_loaded(connection, msg)
        return
    url = fetch_url_for_source(entry.options, msg["source"])
    if url is None:
        connection.send_error(msg["id"], "not_configured", f"No URL for {msg['source']}")
        return

    session = async_get_clientsession(hass)
    try:
        async with asyncio.timeout(FETCH_TIMEOUT):
            async with session.get(
                url, headers={"User-Agent": "HomeAssistant-VA-Rundown"}
            ) as resp:
                body = await resp.content.read(FETCH_MAX_BYTES + 1)
                status = resp.status
                charset = resp.charset or "utf-8"
    except (TimeoutError, aiohttp.ClientError) as err:
        connection.send_error(msg["id"], "fetch_failed", str(err) or type(err).__name__)
        return

    if len(body) > FETCH_MAX_BYTES:
        connection.send_error(msg["id"], "too_large", "Response exceeded size limit")
        return
    if status >= 400:
        connection.send_error(msg["id"], "http_error", f"HTTP {status}")
        return
    connection.send_result(
        msg["id"], {"status": status, "text": body.decode(charset, errors="replace")}
    )
