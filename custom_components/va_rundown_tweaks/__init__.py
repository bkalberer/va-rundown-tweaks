"""View Assist Rundown Tweaks.

Packages the Rundown dashboard, the Rundown-styled View Assist clock view,
the View Assist sidebar menu card and the animated weather-sky background
as one integration configured entirely through its config/options flow.
"""

from __future__ import annotations

from collections.abc import Mapping
import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.start import async_at_started
from homeassistant.helpers.typing import ConfigType

from .const import (
    CONF_CLOCK_BACKGROUND,
    CONF_CLOCK_THERMOSTAT,
    CONF_INSTALL_APP_VIEW,
    CONF_INSTALL_CLOCK_VIEW,
    CONF_LOAD_FONTS,
    CONF_PANEL_ICON,
    CONF_PANEL_TITLE,
    CONF_REGISTER_PANEL,
    CONF_SIDEBAR_MODE,
    CONF_SIDEBAR_POSITION,
    CONF_THERMOSTAT_ENTITY,
    DOMAIN,
    SERVICE_INSTALL_VA_ASSETS,
    SERVICE_REMOVE_VA_ASSETS,
)
from .frontend import (
    async_remove_lovelace_resources,
    async_remove_panel,
    async_sync_lovelace_resources,
    async_sync_panel,
)
from .http import RundownPhotoView, RundownStaticView
from .rundown_config import merged_options
from .view_assist import (
    ViewAssistNotReady,
    async_remove_view_assist,
    async_sync_view_assist,
)
from .websocket import async_register_websocket_commands

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

# Option changes that need server-side work. Everything else is picked up by
# open Rundown pages on their own (they poll the config hash).
FRONTEND_KEYS = frozenset({CONF_LOAD_FONTS, CONF_REGISTER_PANEL, CONF_PANEL_TITLE, CONF_PANEL_ICON})
VIEW_ASSIST_KEYS = frozenset(
    {
        CONF_INSTALL_CLOCK_VIEW,
        CONF_INSTALL_APP_VIEW,
        CONF_SIDEBAR_MODE,
        CONF_SIDEBAR_POSITION,
        CONF_CLOCK_BACKGROUND,
        CONF_CLOCK_THERMOSTAT,
        CONF_THERMOSTAT_ENTITY,
    }
)
DATA_LAST_OPTIONS = f"{DOMAIN}_last_options"


def _loaded_entry(hass: HomeAssistant) -> ConfigEntry:
    entries = hass.config_entries.async_loaded_entries(DOMAIN)
    if not entries:
        raise HomeAssistantError("View Assist Rundown Tweaks is not set up")
    return entries[0]


def _wants_view_assist(options: Mapping[str, Any]) -> bool:
    o = merged_options(options)
    return bool(o[CONF_INSTALL_CLOCK_VIEW] or o[CONF_INSTALL_APP_VIEW] or o[CONF_SIDEBAR_MODE] != "off")


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Register the HTTP views and websocket API (once per run).

    These cannot be unregistered, so each one checks whether a config entry
    is loaded and refuses to work while the integration is disabled.
    """
    hass.http.register_view(RundownStaticView())
    hass.http.register_view(RundownPhotoView())
    async_register_websocket_commands(hass)
    return True


def _async_register_services(hass: HomeAssistant) -> None:
    async def _install(call: ServiceCall) -> None:
        entry = _loaded_entry(hass)
        try:
            await async_sync_view_assist(hass, entry.options, force=call.data["force"])
        except ViewAssistNotReady as err:
            raise HomeAssistantError(str(err)) from err

    async def _remove(call: ServiceCall) -> None:
        try:
            await async_remove_view_assist(hass)
        except ViewAssistNotReady as err:
            raise HomeAssistantError(str(err)) from err

    hass.services.async_register(
        DOMAIN,
        SERVICE_INSTALL_VA_ASSETS,
        _install,
        schema=vol.Schema({vol.Optional("force", default=False): cv.boolean}),
    )
    hass.services.async_register(DOMAIN, SERVICE_REMOVE_VA_ASSETS, _remove)


async def _async_sync_view_assist_quietly(hass: HomeAssistant, entry: ConfigEntry) -> None:
    try:
        await async_sync_view_assist(hass, entry.options)
    except ViewAssistNotReady as err:
        log = _LOGGER.warning if _wants_view_assist(entry.options) else _LOGGER.debug
        log("View Assist changes not applied: %s", err)
    except Exception:
        # Runs from startup and option-update listeners, where an escaping
        # exception would only surface as "Task exception was never retrieved".
        _LOGGER.exception("Could not update the View Assist dashboard")


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up (or resume, after being disabled) View Assist Rundown Tweaks."""
    await async_sync_lovelace_resources(hass, entry.options)
    await async_sync_panel(hass, entry.options)
    _async_register_services(hass)

    # View Assist creates its dashboard during its own startup, so wait until
    # Home Assistant has finished starting before touching it.
    async def _at_started(_hass: HomeAssistant) -> None:
        await _async_sync_view_assist_quietly(hass, entry)

    entry.async_on_unload(async_at_started(hass, _at_started))

    hass.data.setdefault(DATA_LAST_OPTIONS, {})[entry.entry_id] = dict(entry.options)
    entry.async_on_unload(entry.add_update_listener(_async_options_updated))
    return True


async def _async_options_updated(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Apply only the server-side work an option change actually needs."""
    previous = hass.data[DATA_LAST_OPTIONS].get(entry.entry_id, {})
    current = dict(entry.options)
    changed = {k for k in previous.keys() | current.keys() if previous.get(k) != current.get(k)}
    hass.data[DATA_LAST_OPTIONS][entry.entry_id] = current

    if changed & FRONTEND_KEYS:
        await async_sync_lovelace_resources(hass, current)
        await async_sync_panel(hass, current)
    if changed & VIEW_ASSIST_KEYS:
        await _async_sync_view_assist_quietly(hass, entry)


async def _async_withdraw_frontend(hass: HomeAssistant) -> None:
    """Take everything the integration added to the frontend back out."""
    try:
        await async_remove_lovelace_resources(hass)
    except Exception:
        _LOGGER.exception("Could not remove Rundown dashboard resources")
    try:
        await async_remove_view_assist(hass)
    except ViewAssistNotReady:
        pass
    except Exception:
        _LOGGER.exception("Could not remove Rundown views from View Assist")


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry.

    A plain reload only drops the panel and services (setup restores them).
    Disabling also withdraws the dashboard resources and View Assist views
    and sidebar, so nothing of the integration keeps running; the HTTP views
    and websocket API it registered already refuse to serve while no entry
    is loaded. Enabling it again reinstalls everything from the options.
    """
    async_remove_panel(hass)
    for service in (SERVICE_INSTALL_VA_ASSETS, SERVICE_REMOVE_VA_ASSETS):
        hass.services.async_remove(DOMAIN, service)
    hass.data.get(DATA_LAST_OPTIONS, {}).pop(entry.entry_id, None)
    if entry.disabled_by is not None:
        await _async_withdraw_frontend(hass)
    return True


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Remove everything the integration added when it is deleted."""
    await _async_withdraw_frontend(hass)
