"""Config and options flow for View Assist Rundown Tweaks."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
import json
from pathlib import Path
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import callback
from homeassistant.data_entry_flow import section
from homeassistant.helpers import selector as sel
from homeassistant.util.unit_system import US_CUSTOMARY_SYSTEM

from .const import (
    CLOCK_BACKGROUNDS,
    CONF_BG_FOLDER,
    CONF_BG_IMAGES,
    CONF_BG_INTERVAL,
    CONF_BG_SHUFFLE,
    CONF_BROADCAST_ENTITY,
    CONF_BROADCAST_SECONDS,
    CONF_CLOCK_BACKGROUND,
    CONF_CLOCK_THERMOSTAT,
    CONF_CORS_PROXY_FALLBACK,
    CONF_DOOR_ENTITY,
    CONF_DOOR_OPERATOR_ENTITY,
    CONF_ESV_KEY,
    CONF_GRAPH_TOKEN,
    CONF_GRAPH_URL,
    CONF_GRID_COLS,
    CONF_GRID_GAP,
    CONF_GRID_PAD,
    CONF_GRID_ROWS,
    CONF_HIDDEN_WIDGETS,
    CONF_ICS_URL,
    CONF_INSTALL_APP_VIEW,
    CONF_INSTALL_CLOCK_VIEW,
    CONF_LASTFM_KEY,
    CONF_LASTFM_USER,
    CONF_LATITUDE,
    CONF_LAYOUT,
    CONF_LOAD_FONTS,
    CONF_LONGITUDE,
    CONF_MOBILE_BREAKPOINT,
    CONF_MOBILE_DURATIONS,
    CONF_MOBILE_HIDE_ERRORS,
    CONF_MOBILE_MODULES,
    CONF_MOBILE_ORDER,
    CONF_MS_CLIENT_ID,
    CONF_MS_CLIENT_SECRET,
    CONF_MS_LIST_NAME,
    CONF_MS_REFRESH_TOKEN,
    CONF_PANEL_ICON,
    CONF_PANEL_TITLE,
    CONF_REGISTER_PANEL,
    CONF_SIDEBAR_MODE,
    CONF_SIDEBAR_POSITION,
    CONF_TEXT_SCALE,
    CONF_TEXT_SHADOW,
    CONF_THERMOSTAT_ENTITY,
    CONF_TICKER_CUSTOM_LABEL,
    CONF_TICKER_CUSTOM_URL,
    CONF_TICKER_HEIGHT,
    CONF_TICKER_SOURCE,
    CONF_TICKER_SPEED,
    CONF_TODO_ENTITIES,
    CONF_TODO_FILTER,
    CONF_TODO_FUTURE_DAYS,
    CONF_TODO_OVERDUE_DAYS,
    CONF_TODO_SHOW_UNDATED,
    CONF_TODO_SOURCE,
    CONF_UNITS,
    CONF_USE_24H,
    CONF_WEATHER_ENTITY,
    CONF_WEATHER_KEY,
    CONF_WEATHER_SOURCE,
    CONF_WMATA_KEY,
    CONF_WMATA_STATIONS,
    CONF_WX_BROADCAST_STYLE,
    CONF_WX_CITY_NAME,
    CONF_WX_ROTATION,
    CONF_WX_SLIDE_TIMES,
    CONF_WX_SLIDES_ENABLED,
    AUTO_DURATION_MODULES,
    DEFAULT_MOBILE_DURATIONS,
    DOMAIN,
    MOBILE_MODULES,
    SIDEBAR_MODES,
    SIDEBAR_POSITIONS,
    TEXT_SCALES,
    TICKER_SOURCES,
    TITLE,
    TODO_SOURCES,
    UNITS,
    VA_DOMAIN,
    WEATHER_SOURCES,
    WIDGETS,
    WX_SLIDES,
)
from .http import list_photos, resolve_photo_folder
from .rundown_config import (
    is_http_url,
    legacy_from_options,
    merged_options,
    normalize_url,
    options_from_legacy,
    reorder_by_positions,
    sanitize_layout,
)

LEGACY_DEFAULT_PATH = "www/rundown/rundown-config.json"
EXPORT_DEFAULT_PATH = "rundown-config-export.json"
WIDGET_LABELS = {
    "logo": "Logo",
    "clock": "Clock",
    "agenda": "Agenda",
    "metro": "Metro",
    "weather": "Weather",
    "scripture": "Scripture",
    "todo": "To Do",
    "nowplaying": "Now playing",
    "haalerts": "HA alerts",
}
OPTION_MENU = [
    "display",
    "background",
    "weather",
    "ticker",
    "calendar",
    "tasks",
    "transit",
    "scripture",
    "now_playing",
    "alerts",
    "content",
    "view_assist",
    "import_export",
    "save",
]


# ── Selector helpers ──────────────────────────────────────────────────────
def _select(values: list[str], key: str, *, multiple: bool = False) -> sel.SelectSelector:
    return sel.SelectSelector(
        sel.SelectSelectorConfig(
            options=list(values),
            translation_key=key,
            multiple=multiple,
            mode=sel.SelectSelectorMode.LIST if multiple else sel.SelectSelectorMode.DROPDOWN,
        )
    )


def _text(*, multiline: bool = False) -> sel.TextSelector:
    return sel.TextSelector(sel.TextSelectorConfig(multiline=multiline))


def _secret() -> sel.TextSelector:
    return sel.TextSelector(sel.TextSelectorConfig(type=sel.TextSelectorType.PASSWORD))


def _number(
    minimum: float,
    maximum: float,
    *,
    step: float | str = 1,
    unit: str | None = None,
    slider: bool = False,
) -> sel.NumberSelector:
    # NumberSelector validates its config: unit_of_measurement must be a str
    # when present (None is rejected) and step must be >= 0.001 or "any". An
    # invalid selector makes the step fail with a bare "Error" in the UI.
    config = sel.NumberSelectorConfig(
        min=minimum,
        max=maximum,
        step=step,
        mode=sel.NumberSelectorMode.SLIDER if slider else sel.NumberSelectorMode.BOX,
    )
    if unit:
        config["unit_of_measurement"] = unit
    return sel.NumberSelector(config)


def _entity(domain: str | list[str] | None = None, *, multiple: bool = False) -> sel.EntitySelector:
    config: dict[str, Any] = {"multiple": multiple}
    if domain:
        config["domain"] = domain
    return sel.EntitySelector(sel.EntitySelectorConfig(**config))


def _suggest(value: Any) -> dict[str, Any] | None:
    return None if value in (None, "", []) else {"suggested_value": value}


def _optional(key: str, opts: Mapping[str, Any]) -> vol.Optional:
    """Optional field pre-filled with the current value but clearable."""
    return vol.Optional(key, description=_suggest(opts.get(key)))


def _resolve_config_path(config_dir: str, relative: str) -> tuple[Path | None, str | None]:
    """Resolve a config-dir relative file path, refusing anything outside it."""
    base = Path(config_dir).resolve()
    path = (base / str(relative or "").strip().lstrip("/")).resolve()
    if not path.is_relative_to(base):
        return None, "outside_config"
    return path, None


def _in_www(config_dir: str, path: Path) -> bool:
    """True for files under www/, which Home Assistant serves without a login."""
    return path.is_relative_to((Path(config_dir).resolve() / "www"))


def _folder_ok(config_dir: str, relative: str) -> bool:
    base = Path(config_dir).resolve()
    folder = (base / relative).resolve()
    return folder.is_relative_to(base) and folder.is_dir()


class RundownConfigFlow(ConfigFlow, domain=DOMAIN):
    """Initial setup: start fresh or import a standalone rundown-config.json."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> RundownOptionsFlow:
        """Return the options flow."""
        return RundownOptionsFlow()

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Choose how to start."""
        return self.async_show_menu(step_id="user", menu_options=["fresh", "import_legacy"])

    async def async_step_fresh(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Pick the essentials; everything else lives in the options flow."""
        errors: dict[str, str] = {}
        if user_input is not None:
            if user_input[CONF_WEATHER_SOURCE] == "entity" and not user_input.get(CONF_WEATHER_ENTITY):
                errors[CONF_WEATHER_ENTITY] = "weather_entity_required"
            elif user_input[CONF_WEATHER_SOURCE] == "pirateweather" and not user_input.get(CONF_WEATHER_KEY):
                errors[CONF_WEATHER_KEY] = "weather_key_required"
            else:
                options = {
                    CONF_WEATHER_SOURCE: user_input[CONF_WEATHER_SOURCE],
                    CONF_WEATHER_ENTITY: user_input.get(CONF_WEATHER_ENTITY, ""),
                    CONF_WEATHER_KEY: user_input.get(CONF_WEATHER_KEY, ""),
                    CONF_UNITS: user_input[CONF_UNITS],
                    CONF_USE_24H: user_input[CONF_USE_24H],
                }
                return self.async_create_entry(title=TITLE, data={}, options=options)

        schema = vol.Schema(
            {
                vol.Required(CONF_WEATHER_SOURCE, default="entity"): _select(WEATHER_SOURCES, "weather_source"),
                vol.Optional(CONF_WEATHER_ENTITY): _entity("weather"),
                vol.Optional(CONF_WEATHER_KEY): _secret(),
                vol.Required(
                    CONF_UNITS, default="us" if self.hass.config.units is US_CUSTOMARY_SYSTEM else "si"
                ): _select(UNITS, "units"),
                vol.Required(CONF_USE_24H, default=False): sel.BooleanSelector(),
            }
        )
        return self.async_show_form(
            step_id="fresh",
            data_schema=self.add_suggested_values_to_schema(schema, user_input or {}),
            errors=errors,
        )

    async def async_step_import_legacy(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Import an existing standalone rundown-config.json."""
        errors: dict[str, str] = {}
        if user_input is not None:
            relative = user_input["path"].strip().lstrip("/")
            base = Path(self.hass.config.config_dir).resolve()
            path = (base / relative).resolve()

            def _read() -> dict[str, Any] | str:
                if not path.is_relative_to(base):
                    return "outside_config"
                if not path.is_file():
                    return "file_not_found"
                try:
                    data = json.loads(path.read_text(encoding="utf-8"))
                except (OSError, ValueError):
                    return "invalid_json"
                return data if isinstance(data, dict) else "invalid_json"

            result = await self.hass.async_add_executor_job(_read)
            if isinstance(result, str):
                errors["path"] = result
            else:
                legacy_base = str(path.parent.relative_to(base).as_posix())
                options = options_from_legacy(result, legacy_base)
                return self.async_create_entry(title=TITLE, data={}, options=options)

        schema = vol.Schema({vol.Required("path", default=LEGACY_DEFAULT_PATH): _text()})
        return self.async_show_form(step_id="import_legacy", data_schema=schema, errors=errors)


class RundownOptionsFlow(OptionsFlow):
    """Menu-driven options: edit any section, then save once."""

    def __init__(self) -> None:
        """Initialise."""
        self._options: dict[str, Any] | None = None
        self._file_path: str = ""
        self._imported_count: int = 0
        self._exported_secrets: bool = False

    @property
    def _o(self) -> dict[str, Any]:
        if self._options is None:
            self._options = merged_options(self.config_entry.options)
        return self._options

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Show the section menu."""
        return self.async_show_menu(step_id="init", menu_options=OPTION_MENU)

    async def async_step_save(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Persist all edited sections."""
        return self.async_create_entry(data=self._o)

    async def _async_form(
        self,
        step_id: str,
        schema: vol.Schema,
        user_input: dict[str, Any] | None,
        apply: Callable[[dict[str, Any]], None],
        validate: Callable[[dict[str, Any]], Awaitable[dict[str, str]]] | None = None,
        *,
        back: Callable[[], Awaitable[ConfigFlowResult]] | None = None,
    ) -> ConfigFlowResult:
        """Show a section form; on valid submit apply it and return to a menu.

        validate() may set self._error_placeholders for its error messages.
        """
        errors: dict[str, str] = {}
        self._error_placeholders: dict[str, str] = {}
        if user_input is not None:
            errors = await validate(user_input) if validate else {}
            if not errors:
                apply(user_input)
                return await (back or self.async_step_init)()
            schema = self.add_suggested_values_to_schema(schema, user_input)
        return self.async_show_form(
            step_id=step_id,
            data_schema=schema,
            errors=errors,
            description_placeholders=self._error_placeholders or None,
        )

    # ── Display ────────────────────────────────────────────────────────
    async def async_step_display(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Text, units, clock format and mobile breakpoint."""
        o = self._o
        schema = vol.Schema(
            {
                vol.Required(CONF_TEXT_SCALE, default=str(o[CONF_TEXT_SCALE])): _select(TEXT_SCALES, "text_scale"),
                vol.Required(CONF_TEXT_SHADOW, default=o[CONF_TEXT_SHADOW]): sel.BooleanSelector(),
                vol.Required(CONF_USE_24H, default=o[CONF_USE_24H]): sel.BooleanSelector(),
                vol.Required(CONF_UNITS, default=o[CONF_UNITS]): _select(UNITS, "units"),
                vol.Required(CONF_MOBILE_BREAKPOINT, default=o[CONF_MOBILE_BREAKPOINT]): _number(300, 1600, unit="px"),
                vol.Required(CONF_LOAD_FONTS, default=o[CONF_LOAD_FONTS]): sel.BooleanSelector(),
            }
        )

        def apply(data: dict[str, Any]) -> None:
            o.update(data)
            o[CONF_MOBILE_BREAKPOINT] = int(data[CONF_MOBILE_BREAKPOINT])

        return await self._async_form("display", schema, user_input, apply)

    # ── Background ─────────────────────────────────────────────────────
    async def async_step_background(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Photo slideshow."""
        o = self._o
        schema = vol.Schema(
            {
                _optional(CONF_BG_FOLDER, o): _text(),
                _optional(CONF_BG_IMAGES, o): _text(multiline=True),
                vol.Required(CONF_BG_SHUFFLE, default=o[CONF_BG_SHUFFLE]): sel.BooleanSelector(),
                vol.Required(CONF_BG_INTERVAL, default=o[CONF_BG_INTERVAL]): _number(5, 600, unit="s"),
            }
        )

        async def validate(data: dict[str, Any]) -> dict[str, str]:
            folder = (data.get(CONF_BG_FOLDER) or "").strip().strip("/")
            if folder and not await self.hass.async_add_executor_job(
                _folder_ok, self.hass.config.config_dir, folder
            ):
                return {CONF_BG_FOLDER: "folder_not_found"}
            return {}

        def apply(data: dict[str, Any]) -> None:
            o[CONF_BG_FOLDER] = (data.get(CONF_BG_FOLDER) or "").strip().strip("/")
            o[CONF_BG_IMAGES] = data.get(CONF_BG_IMAGES) or ""
            o[CONF_BG_SHUFFLE] = data[CONF_BG_SHUFFLE]
            o[CONF_BG_INTERVAL] = int(data[CONF_BG_INTERVAL])

        return await self._async_form("background", schema, user_input, apply, validate)

    # ── Weather ────────────────────────────────────────────────────────
    async def async_step_weather(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Weather source, location and the forecast rotation."""
        o = self._o
        times = o[CONF_WX_SLIDE_TIMES]
        schema = vol.Schema(
            {
                vol.Required(CONF_WEATHER_SOURCE, default=o[CONF_WEATHER_SOURCE]): _select(WEATHER_SOURCES, "weather_source"),
                _optional(CONF_WEATHER_ENTITY, o): _entity("weather"),
                _optional(CONF_WEATHER_KEY, o): _secret(),
                _optional(CONF_LATITUDE, o): _number(-90, 90, step="any"),
                _optional(CONF_LONGITUDE, o): _number(-180, 180, step="any"),
                vol.Required(CONF_WX_ROTATION, default=o[CONF_WX_ROTATION]): sel.BooleanSelector(),
                vol.Required(CONF_WX_SLIDES_ENABLED, default=o[CONF_WX_SLIDES_ENABLED]): _select(
                    list(WX_SLIDES), "wx_slide", multiple=True
                ),
                vol.Required("slide_times"): section(
                    vol.Schema(
                        {
                            vol.Required(slide, default=int(times.get(slide, 10))): _number(1, 120, unit="s")
                            for slide in WX_SLIDES
                        }
                    ),
                    {"collapsed": True},
                ),
                vol.Required(CONF_WX_BROADCAST_STYLE, default=o[CONF_WX_BROADCAST_STYLE]): sel.BooleanSelector(),
                _optional(CONF_WX_CITY_NAME, o): _text(),
            }
        )

        async def validate(data: dict[str, Any]) -> dict[str, str]:
            if data[CONF_WEATHER_SOURCE] == "entity" and not data.get(CONF_WEATHER_ENTITY):
                return {CONF_WEATHER_ENTITY: "weather_entity_required"}
            if data[CONF_WEATHER_SOURCE] == "pirateweather" and not data.get(CONF_WEATHER_KEY):
                return {CONF_WEATHER_KEY: "weather_key_required"}
            return {}

        def apply(data: dict[str, Any]) -> None:
            o[CONF_WEATHER_SOURCE] = data[CONF_WEATHER_SOURCE]
            o[CONF_WEATHER_ENTITY] = data.get(CONF_WEATHER_ENTITY, "")
            o[CONF_WEATHER_KEY] = data.get(CONF_WEATHER_KEY, "")
            for key in (CONF_LATITUDE, CONF_LONGITUDE):
                if data.get(key) is None:
                    o.pop(key, None)  # fall back to the Home Assistant location
                else:
                    o[key] = float(data[key])
            o[CONF_WX_ROTATION] = data[CONF_WX_ROTATION]
            o[CONF_WX_SLIDES_ENABLED] = data[CONF_WX_SLIDES_ENABLED]
            o[CONF_WX_SLIDE_TIMES] = {k: int(v) for k, v in data["slide_times"].items()}
            o[CONF_WX_BROADCAST_STYLE] = data[CONF_WX_BROADCAST_STYLE]
            o[CONF_WX_CITY_NAME] = data.get(CONF_WX_CITY_NAME, "")

        return await self._async_form("weather", schema, user_input, apply, validate)

    # ── News ticker ────────────────────────────────────────────────────
    async def async_step_ticker(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Headline feed and ticker appearance."""
        o = self._o
        schema = vol.Schema(
            {
                vol.Required(CONF_TICKER_SOURCE, default=o[CONF_TICKER_SOURCE]): _select(TICKER_SOURCES, "ticker_source"),
                _optional(CONF_TICKER_CUSTOM_URL, o): _text(),
                _optional(CONF_TICKER_CUSTOM_LABEL, o): _text(),
                vol.Required(CONF_TICKER_SPEED, default=o[CONF_TICKER_SPEED]): _number(0.1, 5, step=0.05, slider=True),
                _optional(CONF_TICKER_HEIGHT, o): _number(20, 160, unit="px"),
                vol.Required(CONF_CORS_PROXY_FALLBACK, default=o[CONF_CORS_PROXY_FALLBACK]): sel.BooleanSelector(),
            }
        )

        async def validate(data: dict[str, Any]) -> dict[str, str]:
            url = normalize_url(data.get(CONF_TICKER_CUSTOM_URL))
            if url and not is_http_url(url):
                return {CONF_TICKER_CUSTOM_URL: "invalid_url"}
            if data[CONF_TICKER_SOURCE] == "custom" and not url:
                return {CONF_TICKER_CUSTOM_URL: "custom_feed_required"}
            return {}

        def apply(data: dict[str, Any]) -> None:
            o[CONF_TICKER_SOURCE] = data[CONF_TICKER_SOURCE]
            o[CONF_TICKER_CUSTOM_URL] = normalize_url(data.get(CONF_TICKER_CUSTOM_URL))
            o[CONF_TICKER_CUSTOM_LABEL] = data.get(CONF_TICKER_CUSTOM_LABEL) or "News"
            o[CONF_TICKER_SPEED] = float(data[CONF_TICKER_SPEED])
            height = data.get(CONF_TICKER_HEIGHT)
            o[CONF_TICKER_HEIGHT] = None if height is None else int(height)
            o[CONF_CORS_PROXY_FALLBACK] = data[CONF_CORS_PROXY_FALLBACK]

        return await self._async_form("ticker", schema, user_input, apply, validate)

    # ── Calendar ───────────────────────────────────────────────────────
    async def async_step_calendar(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Agenda sources."""
        o = self._o
        schema = vol.Schema(
            {
                _optional(CONF_ICS_URL, o): _secret(),
                _optional(CONF_GRAPH_URL, o): _text(),
                _optional(CONF_GRAPH_TOKEN, o): _secret(),
            }
        )

        async def validate(data: dict[str, Any]) -> dict[str, str]:
            url = normalize_url(data.get(CONF_ICS_URL))
            return {CONF_ICS_URL: "invalid_url"} if url and not is_http_url(url) else {}

        def apply(data: dict[str, Any]) -> None:
            o[CONF_ICS_URL] = normalize_url(data.get(CONF_ICS_URL))
            o[CONF_GRAPH_URL] = data.get(CONF_GRAPH_URL, "")
            o[CONF_GRAPH_TOKEN] = data.get(CONF_GRAPH_TOKEN, "")

        return await self._async_form("calendar", schema, user_input, apply, validate)

    # ── Tasks ──────────────────────────────────────────────────────────
    async def async_step_tasks(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """To-do source and date window."""
        o = self._o
        schema = vol.Schema(
            {
                vol.Required(CONF_TODO_SOURCE, default=o[CONF_TODO_SOURCE]): _select(TODO_SOURCES, "todo_source"),
                _optional(CONF_TODO_ENTITIES, o): _entity("todo", multiple=True),
                _optional(CONF_TODO_FILTER, o): _text(),
                vol.Required(CONF_TODO_OVERDUE_DAYS, default=o[CONF_TODO_OVERDUE_DAYS]): _number(0, 90, unit="d", slider=True),
                vol.Required(CONF_TODO_FUTURE_DAYS, default=o[CONF_TODO_FUTURE_DAYS]): _number(0, 180, unit="d", slider=True),
                vol.Required(CONF_TODO_SHOW_UNDATED, default=o[CONF_TODO_SHOW_UNDATED]): sel.BooleanSelector(),
                vol.Required("microsoft"): section(
                    vol.Schema(
                        {
                            _optional(CONF_MS_CLIENT_ID, o): _text(),
                            _optional(CONF_MS_CLIENT_SECRET, o): _secret(),
                            _optional(CONF_MS_REFRESH_TOKEN, o): _secret(),
                            _optional(CONF_MS_LIST_NAME, o): _text(),
                        }
                    ),
                    {"collapsed": o[CONF_TODO_SOURCE] != "microsoft"},
                ),
            }
        )

        async def validate(data: dict[str, Any]) -> dict[str, str]:
            if data[CONF_TODO_SOURCE] == "microsoft" and not data["microsoft"].get(CONF_MS_CLIENT_ID):
                return {"base": "ms_client_id_required"}
            return {}

        def apply(data: dict[str, Any]) -> None:
            o[CONF_TODO_SOURCE] = data[CONF_TODO_SOURCE]
            o[CONF_TODO_ENTITIES] = data.get(CONF_TODO_ENTITIES, [])
            o[CONF_TODO_FILTER] = data.get(CONF_TODO_FILTER, "")
            o[CONF_TODO_OVERDUE_DAYS] = int(data[CONF_TODO_OVERDUE_DAYS])
            o[CONF_TODO_FUTURE_DAYS] = int(data[CONF_TODO_FUTURE_DAYS])
            o[CONF_TODO_SHOW_UNDATED] = data[CONF_TODO_SHOW_UNDATED]
            for key in (CONF_MS_CLIENT_ID, CONF_MS_CLIENT_SECRET, CONF_MS_REFRESH_TOKEN, CONF_MS_LIST_NAME):
                o[key] = data["microsoft"].get(key, "")

        return await self._async_form("tasks", schema, user_input, apply, validate)

    # ── Transit ────────────────────────────────────────────────────────
    async def async_step_transit(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """WMATA train predictions."""
        o = self._o
        schema = vol.Schema({_optional(CONF_WMATA_KEY, o): _secret(), _optional(CONF_WMATA_STATIONS, o): _text()})

        def apply(data: dict[str, Any]) -> None:
            o[CONF_WMATA_KEY] = data.get(CONF_WMATA_KEY, "")
            o[CONF_WMATA_STATIONS] = ",".join(
                s.strip().upper() for s in str(data.get(CONF_WMATA_STATIONS, "")).split(",") if s.strip()
            )

        return await self._async_form("transit", schema, user_input, apply)

    # ── Scripture ──────────────────────────────────────────────────────
    async def async_step_scripture(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """ESV verse of the day."""
        o = self._o
        schema = vol.Schema({_optional(CONF_ESV_KEY, o): _secret()})

        def apply(data: dict[str, Any]) -> None:
            o[CONF_ESV_KEY] = data.get(CONF_ESV_KEY, "")

        return await self._async_form("scripture", schema, user_input, apply)

    # ── Now playing ────────────────────────────────────────────────────
    async def async_step_now_playing(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Last.fm now playing."""
        o = self._o
        schema = vol.Schema(
            {
                _optional(CONF_LASTFM_KEY, o): _secret(),
                _optional(CONF_LASTFM_USER, o): _text(),
            }
        )

        def apply(data: dict[str, Any]) -> None:
            for key in (CONF_LASTFM_KEY, CONF_LASTFM_USER):
                o[key] = data.get(key, "")

        return await self._async_form("now_playing", schema, user_input, apply)

    # ── Home Assistant alerts ──────────────────────────────────────────
    async def async_step_alerts(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Door alert, broadcast and thermostat readout."""
        o = self._o
        schema = vol.Schema(
            {
                _optional(CONF_DOOR_ENTITY, o): _entity(["binary_sensor", "cover"]),
                _optional(CONF_DOOR_OPERATOR_ENTITY, o): _entity(),
                _optional(CONF_BROADCAST_ENTITY, o): _entity(["input_text", "text", "sensor"]),
                vol.Required(CONF_BROADCAST_SECONDS, default=o[CONF_BROADCAST_SECONDS]): _number(5, 120, unit="s"),
                _optional(CONF_THERMOSTAT_ENTITY, o): _entity("climate"),
            }
        )

        def apply(data: dict[str, Any]) -> None:
            for key in (CONF_DOOR_ENTITY, CONF_DOOR_OPERATOR_ENTITY, CONF_BROADCAST_ENTITY, CONF_THERMOSTAT_ENTITY):
                o[key] = data.get(key, "")
            o[CONF_BROADCAST_SECONDS] = int(data[CONF_BROADCAST_SECONDS])

        return await self._async_form("alerts", schema, user_input, apply)

    # ── Content ─────────────────────────────────────────────────────────
    async def async_step_content(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Choose between the full screen and small screen content forms."""
        return self.async_show_menu(
            step_id="content", menu_options=["content_full_screen", "content_small_screen", "init"]
        )

    async def async_step_content_full_screen(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Grid size and, per widget, visibility and placement."""
        o = self._o
        layout = sanitize_layout(o[CONF_LAYOUT])
        hidden = set(o[CONF_HIDDEN_WIDGETS])
        fields: dict[Any, Any] = {
            vol.Required(CONF_GRID_COLS, default=o[CONF_GRID_COLS]): _number(4, 32),
            vol.Required(CONF_GRID_ROWS, default=o[CONF_GRID_ROWS]): _number(4, 24),
            vol.Required(CONF_GRID_GAP, default=o[CONF_GRID_GAP]): _text(),
            vol.Required(CONF_GRID_PAD, default=o[CONF_GRID_PAD]): _text(),
        }
        for widget in WIDGETS:
            pos = layout[widget]
            fields[vol.Required(f"widget_{widget}")] = section(
                vol.Schema(
                    {
                        vol.Required("show", default=widget not in hidden): sel.BooleanSelector(),
                        vol.Required("column", default=pos["cs"]): _number(1, 32),
                        vol.Required("row", default=pos["rs"]): _number(1, 24),
                        vol.Required("width", default=pos["ce"] - pos["cs"]): _number(1, 32),
                        vol.Required("height", default=pos["re"] - pos["rs"]): _number(1, 24),
                    }
                ),
                {"collapsed": True},
            )
        schema = vol.Schema(fields)

        async def validate(data: dict[str, Any]) -> dict[str, str]:
            cols, rows = int(data[CONF_GRID_COLS]), int(data[CONF_GRID_ROWS])
            for widget in WIDGETS:
                cell = data[f"widget_{widget}"]
                if (
                    int(cell["column"]) + int(cell["width"]) - 1 > cols
                    or int(cell["row"]) + int(cell["height"]) - 1 > rows
                ):
                    self._error_placeholders = {"widget": WIDGET_LABELS[widget]}
                    return {"base": "widget_outside_grid"}
            return {}

        def apply(data: dict[str, Any]) -> None:
            o[CONF_GRID_COLS] = int(data[CONF_GRID_COLS])
            o[CONF_GRID_ROWS] = int(data[CONF_GRID_ROWS])
            o[CONF_GRID_GAP] = data[CONF_GRID_GAP]
            o[CONF_GRID_PAD] = data[CONF_GRID_PAD]
            o[CONF_HIDDEN_WIDGETS] = [w for w in WIDGETS if not data[f"widget_{w}"]["show"]]
            o[CONF_LAYOUT] = sanitize_layout(
                {
                    w: {
                        "cs": int(cell["column"]),
                        "ce": int(cell["column"]) + int(cell["width"]),
                        "rs": int(cell["row"]),
                        "re": int(cell["row"]) + int(cell["height"]),
                    }
                    for w in WIDGETS
                    for cell in [data[f"widget_{w}"]]
                }
            )

        return await self._async_form(
            "content_full_screen", schema, user_input, apply, validate, back=self.async_step_content
        )

    async def async_step_content_small_screen(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Which sections rotate, in what order, and for how long."""
        o = self._o
        order = list(o[CONF_MOBILE_ORDER])
        enabled = set(o[CONF_MOBILE_MODULES])
        durations = {**DEFAULT_MOBILE_DURATIONS, **(o[CONF_MOBILE_DURATIONS] or {})}
        fields: dict[Any, Any] = {
            vol.Required(CONF_MOBILE_HIDE_ERRORS, default=o[CONF_MOBILE_HIDE_ERRORS]): sel.BooleanSelector(),
        }
        # Sections are listed in their current rotation order.
        for module in order:
            fields[vol.Required(f"slide_{module}")] = section(
                vol.Schema(
                    {
                        vol.Required("show", default=module in enabled): sel.BooleanSelector(),
                        vol.Required("position", default=order.index(module) + 1): _number(
                            1, len(MOBILE_MODULES)
                        ),
                        vol.Required("duration", default=int(durations.get(module, 10))): _number(
                            0 if module in AUTO_DURATION_MODULES else 1, 600, unit="s"
                        ),
                    }
                ),
                {"collapsed": True},
            )
        schema = vol.Schema(fields)

        async def validate(data: dict[str, Any]) -> dict[str, str]:
            if not any(data[f"slide_{m}"]["show"] for m in MOBILE_MODULES):
                return {"base": "no_slides"}
            return {}

        def apply(data: dict[str, Any]) -> None:
            ranked = reorder_by_positions(
                order, {m: int(data[f"slide_{m}"]["position"]) for m in MOBILE_MODULES}
            )
            o[CONF_MOBILE_ORDER] = ranked
            o[CONF_MOBILE_MODULES] = [m for m in ranked if data[f"slide_{m}"]["show"]]
            o[CONF_MOBILE_DURATIONS] = {m: int(data[f"slide_{m}"]["duration"]) for m in MOBILE_MODULES}
            o[CONF_MOBILE_HIDE_ERRORS] = data[CONF_MOBILE_HIDE_ERRORS]

        return await self._async_form(
            "content_small_screen", schema, user_input, apply, validate, back=self.async_step_content
        )

    # ── Import / export ────────────────────────────────────────────────
    async def async_step_import_export(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Import from, or export to, a standalone rundown-config.json."""
        return self.async_show_menu(
            step_id="import_export", menu_options=["import_settings", "export_settings", "init"]
        )

    async def async_step_import_settings(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Merge a rundown-config.json into the settings being edited."""
        errors: dict[str, str] = {}
        if user_input is not None:
            path, error = _resolve_config_path(self.hass.config.config_dir, user_input["path"])

            def _read() -> dict[str, Any] | str:
                if not path.is_file():
                    return "file_not_found"
                try:
                    data = json.loads(path.read_text(encoding="utf-8"))
                except (OSError, ValueError):
                    return "invalid_json"
                return data if isinstance(data, dict) else "invalid_json"

            result = error or await self.hass.async_add_executor_job(_read)
            if isinstance(result, str):
                errors["path"] = result
            else:
                base = Path(self.hass.config.config_dir).resolve()
                imported = options_from_legacy(result, str(path.parent.relative_to(base).as_posix()))
                self._o.update(imported)
                self._file_path = str(path.relative_to(base).as_posix())
                self._imported_count = len(imported)
                return await self.async_step_import_done()

        schema = vol.Schema({vol.Required("path", default=LEGACY_DEFAULT_PATH): _text()})
        return self.async_show_form(step_id="import_settings", data_schema=schema, errors=errors)

    async def async_step_import_done(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Confirm what was imported; nothing is stored until Save."""
        if user_input is not None:
            return await self.async_step_init()
        return self.async_show_form(
            step_id="import_done",
            data_schema=vol.Schema({}),
            description_placeholders={"path": self._file_path, "count": str(self._imported_count)},
        )

    async def async_step_export_settings(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Write the settings being edited to a rundown-config.json."""
        errors: dict[str, str] = {}
        if user_input is not None:
            config_dir = self.hass.config.config_dir
            path, error = _resolve_config_path(config_dir, user_input["path"])
            include_secrets = user_input["include_secrets"]
            if error:
                errors["path"] = error
            elif include_secrets and _in_www(config_dir, path):
                # Anything under www/ can be downloaded without signing in.
                errors["path"] = "secrets_in_www"
            else:

                def _write() -> str | None:
                    folder = resolve_photo_folder(self.hass, self._o.get(CONF_BG_FOLDER))
                    data = legacy_from_options(
                        self._o, photo_names=list_photos(folder), include_secrets=include_secrets
                    )
                    try:
                        path.parent.mkdir(parents=True, exist_ok=True)
                        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
                    except OSError:
                        return "write_failed"
                    return None

                if write_error := await self.hass.async_add_executor_job(_write):
                    errors["path"] = write_error
                else:
                    base = Path(config_dir).resolve()
                    self._file_path = str(path.relative_to(base).as_posix())
                    self._exported_secrets = include_secrets
                    return await self.async_step_export_done()

        schema = vol.Schema(
            {
                vol.Required("path", default=EXPORT_DEFAULT_PATH): _text(),
                vol.Required("include_secrets", default=True): sel.BooleanSelector(),
            }
        )
        return self.async_show_form(
            step_id="export_settings",
            data_schema=self.add_suggested_values_to_schema(schema, user_input or {}),
            errors=errors,
        )

    async def async_step_export_done(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Confirm where the file was written."""
        if user_input is not None:
            return await self.async_step_init()
        return self.async_show_form(
            step_id="export_done",
            data_schema=vol.Schema({}),
            description_placeholders={
                "path": self._file_path,
                "secrets": "included" if self._exported_secrets else "left out",
            },
        )

    # ── View Assist & panel ────────────────────────────────────────────
    async def async_step_view_assist(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Sidebar panel, View Assist views, sidebar menu and clock background."""
        o = self._o
        schema = vol.Schema(
            {
                vol.Required(CONF_REGISTER_PANEL, default=o[CONF_REGISTER_PANEL]): sel.BooleanSelector(),
                vol.Required(CONF_PANEL_TITLE, default=o[CONF_PANEL_TITLE]): _text(),
                vol.Required(CONF_PANEL_ICON, default=o[CONF_PANEL_ICON]): sel.IconSelector(),
                vol.Required(CONF_INSTALL_APP_VIEW, default=o[CONF_INSTALL_APP_VIEW]): sel.BooleanSelector(),
                vol.Required(CONF_INSTALL_CLOCK_VIEW, default=o[CONF_INSTALL_CLOCK_VIEW]): sel.BooleanSelector(),
                vol.Required(CONF_CLOCK_BACKGROUND, default=o[CONF_CLOCK_BACKGROUND]): _select(
                    CLOCK_BACKGROUNDS, "clock_background"
                ),
                vol.Required(CONF_CLOCK_THERMOSTAT, default=o[CONF_CLOCK_THERMOSTAT]): sel.BooleanSelector(),
                vol.Required(CONF_SIDEBAR_MODE, default=o[CONF_SIDEBAR_MODE]): _select(SIDEBAR_MODES, "sidebar_mode"),
                vol.Required(CONF_SIDEBAR_POSITION, default=o[CONF_SIDEBAR_POSITION]): _select(
                    SIDEBAR_POSITIONS, "sidebar_position"
                ),
            }
        )

        async def validate(data: dict[str, Any]) -> dict[str, str]:
            wants_va = data[CONF_INSTALL_CLOCK_VIEW] or data[CONF_INSTALL_APP_VIEW] or data[CONF_SIDEBAR_MODE] != "off"
            if wants_va and not self.hass.config_entries.async_entries(VA_DOMAIN):
                return {"base": "view_assist_missing"}
            return {}

        def apply(data: dict[str, Any]) -> None:
            o.update(data)

        return await self._async_form("view_assist", schema, user_input, apply, validate)
