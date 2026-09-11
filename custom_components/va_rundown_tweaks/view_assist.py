"""Install the Rundown clock/app views and sidebar into View Assist.

Views are written to config/view_assist/views/<name>/<name>.yaml and added
to the View Assist dashboard the same way View Assist installs its own views
(a panel view holding the view card). As with View Assist's views, a
user_<name>.yaml next to it takes precedence, and `view_assist.save_asset`
can back it up.

The all-views sidebar is added as one extra button-card template on the View
Assist dashboard. View Assist records dashboard edits in user_dashboard.yaml,
so the change survives View Assist dashboard updates, and removing this
integration takes it back out.
"""

from __future__ import annotations

from collections.abc import Mapping
import copy
import logging
from pathlib import Path
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.util.yaml import load_yaml_dict, save_yaml

from .const import (
    CONF_CLOCK_BACKGROUND,
    CONF_CLOCK_THERMOSTAT,
    CONF_INSTALL_APP_VIEW,
    CONF_INSTALL_CLOCK_VIEW,
    CONF_SIDEBAR_MODE,
    CONF_SIDEBAR_POSITION,
    CONF_THERMOSTAT_ENTITY,
    FRONTEND_VERSION,
    STATIC_URL,
    VA_APP_VIEW,
    VA_CLOCK_VIEW,
    VA_DASHBOARD_KEY,
    VA_DOMAIN,
    VA_NAVBAR_TEMPLATE,
)
from .rundown_config import merged_options

_LOGGER = logging.getLogger(__name__)

TEMPLATE_DIR = Path(__file__).parent / "view_templates"
VIEW_TITLES = {VA_CLOCK_VIEW: "Rundown Tweaks Clock", VA_APP_VIEW: "Rundown Tweaks"}
MENU_CARD = "custom:view-assist-menu-card"
SIDEBAR_PAD = "clamp(70px, 9vw, 110px)"


class ViewAssistNotReady(HomeAssistantError):
    """View Assist is not installed or its dashboard does not exist yet."""


def _dashboard_store(hass: HomeAssistant):
    lovelace = hass.data.get("lovelace")
    store = lovelace.dashboards.get(VA_DASHBOARD_KEY) if lovelace else None
    if store is None:
        raise ViewAssistNotReady(
            "View Assist (with its master configuration and dashboard) must be set up first"
        )
    return store


def _menu_card(position: str) -> dict[str, Any]:
    return {"card": {"type": MENU_CARD, "position": position, "reverse": True}}


def _contains_menu_card(node: Any) -> bool:
    if isinstance(node, Mapping):
        return node.get("type") == MENU_CARD or any(_contains_menu_card(v) for v in node.values())
    if isinstance(node, list):
        return any(_contains_menu_card(v) for v in node)
    return False


def _body_template_names(templates: Mapping[str, Any]) -> list[str]:
    names = (templates.get("body_template") or {}).get("template") or []
    return [names] if isinstance(names, str) else list(names)


def foreign_sidebar_present(dashboard: Mapping[str, Any]) -> bool:
    """True if body_template already pulls in a menu card we did not add."""
    templates = dashboard.get("button_card_templates") or {}
    return any(
        name != VA_NAVBAR_TEMPLATE and _contains_menu_card(templates.get(name))
        for name in _body_template_names(templates)
    )


def build_clock_view(template: dict[str, Any], options: Mapping[str, Any], *, sidebar_elsewhere: bool) -> dict[str, Any]:
    """Fill the rundowntweaksclock template's variables from the options."""
    o = merged_options(options)
    view = copy.deepcopy(template)
    mode = o[CONF_SIDEBAR_MODE]
    variables = view.setdefault("variables", {})
    variables[f"{VA_CLOCK_VIEW}version"] = FRONTEND_VERSION
    variables["var_rundown_thermostat"] = (
        o[CONF_THERMOSTAT_ENTITY] if o[CONF_CLOCK_THERMOSTAT] else ""
    )
    variables["var_rundown_background"] = o[CONF_CLOCK_BACKGROUND]
    variables["var_rundown_sky_url"] = f"{STATIC_URL}/sky.html?v={FRONTEND_VERSION}"
    has_sidebar = mode != "off" or sidebar_elsewhere
    variables["var_rundown_sidebar_pad"] = SIDEBAR_PAD if has_sidebar else "0px"
    variables["var_rundown_sidebar_side"] = o[CONF_SIDEBAR_POSITION]
    fields = view.setdefault("custom_fields", {})
    if mode == "clock_view":
        fields["rundown_navbar"] = _menu_card(o[CONF_SIDEBAR_POSITION])
    else:
        fields.pop("rundown_navbar", None)
    return view


def build_app_view(template: dict[str, Any]) -> dict[str, Any]:
    """Stamp the version onto the rundown app view."""
    view = copy.deepcopy(template)
    view.setdefault("variables", {})[f"{VA_APP_VIEW}version"] = FRONTEND_VERSION
    return view


async def _async_install_view(hass: HomeAssistant, name: str, view: dict[str, Any], force: bool) -> None:
    """Write the view file and put the view on the View Assist dashboard.

    This mirrors what View Assist's own view installer does (a panel view
    whose single card is the view config) rather than calling
    view_assist.load_asset: that action looks the view up in the View
    Assist GitHub repository afterwards and raises for any view that is not
    part of it.
    """
    store = _dashboard_store(hass)
    folder = Path(hass.config.path(VA_DOMAIN, "views", name))

    def _write_and_choose() -> dict[str, Any]:
        path = folder / f"{name}.yaml"
        try:
            unchanged = path.exists() and load_yaml_dict(path) == view
        except HomeAssistantError:
            unchanged = False
        if force or not unchanged:
            folder.mkdir(parents=True, exist_ok=True)
            save_yaml(str(path), view)
        # Same precedence View Assist uses: a user_ copy overrides.
        user_path = folder / f"user_{name}.yaml"
        if user_path.exists():
            try:
                return load_yaml_dict(user_path)
            except HomeAssistantError as err:
                _LOGGER.warning("Ignoring unreadable %s: %s", user_path, err)
        return view

    card = await hass.async_add_executor_job(_write_and_choose)
    new_view = {"type": "panel", "title": VIEW_TITLES[name], "path": name, "cards": [card]}

    dashboard = copy.deepcopy(await store.async_load(False))
    views = dashboard.get("views") or []
    for index, existing in enumerate(views):
        if existing.get("path") == name:
            if existing == new_view and not force:
                return
            views[index] = new_view
            break
    else:
        views.append(new_view)
    dashboard["views"] = views
    _LOGGER.debug("Installing View Assist view %s", name)
    await store.async_save(dashboard)


async def _async_remove_view(hass: HomeAssistant, name: str) -> None:
    store = _dashboard_store(hass)
    dashboard = copy.deepcopy(await store.async_load(False))
    views = dashboard.get("views") or []
    kept = [v for v in views if v.get("path") != name]
    if len(kept) != len(views):
        dashboard["views"] = kept
        await store.async_save(dashboard)

    path = Path(hass.config.path(VA_DOMAIN, "views", name, f"{name}.yaml"))

    def _delete() -> None:
        # Only delete a file this integration wrote (it carries our version key).
        try:
            if path.exists() and f"{name}version" in (load_yaml_dict(path).get("variables") or {}):
                path.unlink()
        except (HomeAssistantError, OSError) as err:
            _LOGGER.debug("Could not remove %s: %s", path, err)

    await hass.async_add_executor_job(_delete)


async def _async_sync_sidebar(hass: HomeAssistant, options: Mapping[str, Any]) -> None:
    o = merged_options(options)
    store = _dashboard_store(hass)
    dashboard = copy.deepcopy(await store.async_load(False))
    templates = dashboard.setdefault("button_card_templates", {})
    body = templates.get("body_template")
    if not isinstance(body, dict):
        _LOGGER.warning("View Assist dashboard has no body_template; sidebar not installed")
        return
    names = _body_template_names(templates)
    want = o[CONF_SIDEBAR_MODE] == "all_views"

    if want and foreign_sidebar_present(dashboard):
        _LOGGER.warning(
            "A view-assist-menu-card is already added to body_template by another "
            "template; not adding a second sidebar"
        )
        want = False

    new_template = {
        "template": ["variable_template", "responsive_base"],
        "custom_fields": {"rundown_navbar": _menu_card(o[CONF_SIDEBAR_POSITION])},
    }
    changed = False
    if want:
        if templates.get(VA_NAVBAR_TEMPLATE) != new_template:
            templates[VA_NAVBAR_TEMPLATE] = new_template
            changed = True
        if VA_NAVBAR_TEMPLATE not in names:
            body["template"] = [*names, VA_NAVBAR_TEMPLATE]
            changed = True
    else:
        if VA_NAVBAR_TEMPLATE in names:
            body["template"] = [n for n in names if n != VA_NAVBAR_TEMPLATE]
            changed = True
        if templates.pop(VA_NAVBAR_TEMPLATE, None) is not None:
            changed = True

    if changed:
        await store.async_save(dashboard)


async def async_sync_view_assist(hass: HomeAssistant, options: Mapping[str, Any], *, force: bool = False) -> None:
    """Bring the View Assist dashboard in line with the options."""
    o = merged_options(options)
    store = _dashboard_store(hass)
    sidebar_elsewhere = foreign_sidebar_present(await store.async_load(False))

    await _async_sync_sidebar(hass, o)

    if o[CONF_INSTALL_CLOCK_VIEW]:
        template = await hass.async_add_executor_job(load_yaml_dict, TEMPLATE_DIR / f"{VA_CLOCK_VIEW}.yaml")
        await _async_install_view(
            hass, VA_CLOCK_VIEW, build_clock_view(template, o, sidebar_elsewhere=sidebar_elsewhere), force
        )
    else:
        await _async_remove_view(hass, VA_CLOCK_VIEW)

    if o[CONF_INSTALL_APP_VIEW]:
        template = await hass.async_add_executor_job(load_yaml_dict, TEMPLATE_DIR / f"{VA_APP_VIEW}.yaml")
        await _async_install_view(hass, VA_APP_VIEW, build_app_view(template), force)
    else:
        await _async_remove_view(hass, VA_APP_VIEW)


async def async_remove_view_assist(hass: HomeAssistant) -> None:
    """Take every View Assist change this integration made back out."""
    off = {CONF_INSTALL_CLOCK_VIEW: False, CONF_INSTALL_APP_VIEW: False, CONF_SIDEBAR_MODE: "off"}
    await async_sync_view_assist(hass, off)
