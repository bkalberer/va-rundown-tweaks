"""Constants for View Assist Rundown Tweaks."""

from __future__ import annotations

from typing import Any, Final

DOMAIN: Final = "va_rundown_tweaks"
TITLE: Final = "View Assist Rundown Tweaks"
VA_DOMAIN: Final = "view_assist"

# Bump whenever anything under www/ changes so Lovelace resources and the
# panel iframe URL are cache-busted.
FRONTEND_VERSION: Final = "0.2.0"

STATIC_URL: Final = f"/{DOMAIN}/static"
PHOTO_URL: Final = f"/api/{DOMAIN}/photo"
PANEL_URL_PATH: Final = "va-rundown-tweaks"
PANEL_COMPONENT: Final = "va-rundown-tweaks-panel"

# Lovelace resources this integration manages (served from www/).
LOVELACE_MODULES: Final = (
    "rundown-wx-icon.js",
    "view-assist-menu-card.js",
    "va-rundown-tweaks-card.js",
)

# View Assist view names installed by this integration. View Assist reads a
# view's version from variables.<name>version, so names stay alphanumeric.
VA_CLOCK_VIEW: Final = "rundowntweaksclock"
VA_APP_VIEW: Final = "rundowntweaks"
VA_DASHBOARD_KEY: Final = "view-assist"
VA_NAVBAR_TEMPLATE: Final = "rundown_tweaks_navbar_overlay"

IMAGE_EXTENSIONS: Final = (".jpg", ".jpeg", ".png", ".webp", ".gif", ".avif")

# ── Option keys ───────────────────────────────────────────────────────────
# Display
CONF_TEXT_SCALE = "text_scale"
CONF_TEXT_SHADOW = "text_shadow"
CONF_USE_24H = "use_24h"
CONF_UNITS = "units"
CONF_MOBILE_BREAKPOINT = "mobile_breakpoint"
CONF_LOAD_FONTS = "load_fonts"

# Background
CONF_BG_FOLDER = "bg_folder"
CONF_BG_IMAGES = "bg_images"
CONF_BG_SHUFFLE = "bg_shuffle"
CONF_BG_INTERVAL = "bg_interval"

# Weather
CONF_WEATHER_SOURCE = "weather_source"
CONF_WEATHER_KEY = "weather_key"
CONF_WEATHER_ENTITY = "weather_entity"
CONF_LATITUDE = "latitude"
CONF_LONGITUDE = "longitude"
CONF_WX_ROTATION = "wx_rotation_enabled"
CONF_WX_SLIDES_ENABLED = "wx_slides_enabled"
CONF_WX_SLIDE_ORDER = "wx_slide_order"
CONF_WX_SLIDE_TIMES = "wx_slide_times"
CONF_WX_BROADCAST_STYLE = "wx_broadcast_style"
CONF_WX_CITY_NAME = "wx_city_name"

# News ticker
CONF_TICKER_SOURCE = "ticker_source"
CONF_TICKER_CUSTOM_URL = "ticker_custom_url"
CONF_TICKER_CUSTOM_LABEL = "ticker_custom_label"
CONF_TICKER_SPEED = "ticker_speed"
CONF_TICKER_HEIGHT = "ticker_height"
CONF_CORS_PROXY_FALLBACK = "cors_proxy_fallback"

# Transit (WMATA)
CONF_WMATA_KEY = "wmata_key"
CONF_WMATA_STATIONS = "wmata_stations"

# Calendar
CONF_ICS_URL = "ics_url"
CONF_GRAPH_URL = "graph_url"
CONF_GRAPH_TOKEN = "graph_token"

# Scripture
CONF_ESV_KEY = "esv_key"

# Now playing
CONF_LASTFM_KEY = "lastfm_key"
CONF_LASTFM_USER = "lastfm_user"

# Tasks
CONF_TODO_SOURCE = "todo_source"
CONF_TODO_ENTITIES = "todo_entities"
CONF_TODO_FILTER = "todo_filter"
CONF_TODO_OVERDUE_DAYS = "todo_overdue_days"
CONF_TODO_FUTURE_DAYS = "todo_future_days"
CONF_TODO_SHOW_UNDATED = "todo_show_undated"
CONF_MS_CLIENT_ID = "ms_client_id"
CONF_MS_CLIENT_SECRET = "ms_client_secret"
CONF_MS_REFRESH_TOKEN = "ms_refresh_token"
CONF_MS_LIST_NAME = "ms_list_name"

# Home Assistant alerts / readouts
CONF_DOOR_ENTITY = "door_entity"
CONF_DOOR_OPERATOR_ENTITY = "door_operator_entity"
CONF_BROADCAST_ENTITY = "broadcast_entity"
CONF_BROADCAST_SECONDS = "broadcast_seconds"
CONF_THERMOSTAT_ENTITY = "thermostat_entity"

# Layout
CONF_GRID_COLS = "grid_cols"
CONF_GRID_ROWS = "grid_rows"
CONF_GRID_GAP = "grid_gap"
CONF_GRID_PAD = "grid_pad"
CONF_LAYOUT = "layout"
CONF_HIDDEN_WIDGETS = "hidden_widgets"
CONF_MOBILE_MODULES = "mobile_modules"
CONF_MOBILE_DURATIONS = "mobile_durations"
CONF_MOBILE_ORDER = "mobile_order"
CONF_MOBILE_HIDE_ERRORS = "mobile_hide_errors"

# View Assist / frontend integration
CONF_REGISTER_PANEL = "register_panel"
CONF_PANEL_TITLE = "panel_title"
CONF_PANEL_ICON = "panel_icon"
CONF_INSTALL_CLOCK_VIEW = "install_clock_view"
CONF_INSTALL_APP_VIEW = "install_app_view"
CONF_SIDEBAR_MODE = "sidebar_mode"
CONF_SIDEBAR_POSITION = "sidebar_position"
CONF_CLOCK_BACKGROUND = "clock_background"
CONF_CLOCK_THERMOSTAT = "clock_thermostat"

# ── Choice values ─────────────────────────────────────────────────────────
WEATHER_SOURCES = ["entity", "pirateweather"]
UNITS = ["us", "si"]
TEXT_SCALES = ["1", "1.15", "1.3"]
TICKER_SOURCES = ["wtop", "san", "custom"]
TODO_SOURCES = ["none", "home_assistant", "microsoft"]
SIDEBAR_MODES = ["off", "clock_view", "all_views"]
SIDEBAR_POSITIONS = ["right", "left"]
CLOCK_BACKGROUNDS = ["view_assist", "sky"]

WIDGETS = [
    "logo",
    "clock",
    "agenda",
    "metro",
    "weather",
    "scripture",
    "todo",
    "nowplaying",
    "haalerts",
]
MOBILE_MODULES = [
    "clock",
    "weather",
    "agenda",
    "metro",
    "todo",
    "scripture",
    "nowplaying",
    "haalerts",
]
WX_SLIDES: dict[str, str] = {
    "h1": "Next 12 Hours",
    "h2": "Tomorrow Morning",
    "h3": "Tomorrow Night",
    "daily": "5-Day Forecast",
    "almanac": "Almanac",
    "moon": "Moon Phase",
    "sun": "Sunrise/Sunset",
}

DEFAULT_LAYOUT: dict[str, dict[str, int]] = {
    "logo": {"cs": 1, "ce": 3, "rs": 1, "re": 2},
    "clock": {"cs": 3, "ce": 9, "rs": 1, "re": 2},
    "agenda": {"cs": 1, "ce": 4, "rs": 2, "re": 9},
    "metro": {"cs": 4, "ce": 9, "rs": 2, "re": 9},
    "weather": {"cs": 9, "ce": 13, "rs": 1, "re": 9},
    "scripture": {"cs": 1, "ce": 5, "rs": 3, "re": 6},
    "todo": {"cs": 5, "ce": 9, "rs": 3, "re": 7},
    "nowplaying": {"cs": 13, "ce": 17, "rs": 1, "re": 3},
    "haalerts": {"cs": 13, "ce": 17, "rs": 1, "re": 3},
}

DEFAULT_MOBILE_DURATIONS: dict[str, int] = {
    "clock": 8,
    "weather": 0,  # 0 = automatic: the sum of its forecast products
    "haalerts": 0,  # 0 = stay until the alert clears
    "agenda": 12,
    "metro": 10,
    "todo": 10,
    "scripture": 11,
    "nowplaying": 10,
}

# Small-screen sections whose duration accepts 0 ("automatic").
AUTO_DURATION_MODULES: Final = ("weather", "haalerts")

DEFAULT_WX_SLIDE_TIMES: dict[str, int] = {
    "h1": 10,
    "h2": 10,
    "h3": 10,
    "daily": 15,
    "almanac": 10,
    "moon": 10,
    "sun": 10,
}

DEFAULTS: dict[str, Any] = {
    CONF_TEXT_SCALE: "1",
    CONF_TEXT_SHADOW: True,
    CONF_USE_24H: False,
    CONF_UNITS: "us",
    CONF_MOBILE_BREAKPOINT: 600,
    CONF_LOAD_FONTS: True,
    CONF_BG_FOLDER: "",
    CONF_BG_IMAGES: "",
    CONF_BG_SHUFFLE: False,
    CONF_BG_INTERVAL: 22,
    CONF_WEATHER_SOURCE: "entity",
    CONF_WEATHER_KEY: "",
    CONF_WEATHER_ENTITY: "",
    CONF_WX_ROTATION: True,
    CONF_WX_SLIDES_ENABLED: list(WX_SLIDES),
    CONF_WX_SLIDE_ORDER: list(WX_SLIDES),
    CONF_WX_SLIDE_TIMES: DEFAULT_WX_SLIDE_TIMES,
    CONF_WX_BROADCAST_STYLE: False,
    CONF_WX_CITY_NAME: "",
    CONF_TICKER_SOURCE: "wtop",
    CONF_TICKER_CUSTOM_URL: "",
    CONF_TICKER_CUSTOM_LABEL: "News",
    CONF_TICKER_SPEED: 0.55,
    CONF_TICKER_HEIGHT: 34,
    CONF_CORS_PROXY_FALLBACK: False,
    CONF_WMATA_KEY: "",
    CONF_WMATA_STATIONS: "",
    CONF_ICS_URL: "",
    CONF_GRAPH_URL: "",
    CONF_GRAPH_TOKEN: "",
    CONF_ESV_KEY: "",
    CONF_LASTFM_KEY: "",
    CONF_LASTFM_USER: "",
    CONF_TODO_SOURCE: "none",
    CONF_TODO_ENTITIES: [],
    CONF_TODO_FILTER: "",
    CONF_TODO_OVERDUE_DAYS: 90,
    CONF_TODO_FUTURE_DAYS: 180,
    CONF_TODO_SHOW_UNDATED: True,
    CONF_MS_CLIENT_ID: "",
    CONF_MS_CLIENT_SECRET: "",
    CONF_MS_REFRESH_TOKEN: "",
    CONF_MS_LIST_NAME: "",
    CONF_DOOR_ENTITY: "",
    CONF_DOOR_OPERATOR_ENTITY: "",
    CONF_BROADCAST_ENTITY: "",
    CONF_BROADCAST_SECONDS: 15,
    CONF_THERMOSTAT_ENTITY: "",
    CONF_GRID_COLS: 16,
    CONF_GRID_ROWS: 10,
    CONF_GRID_GAP: "clamp(6px, 0.6vw, 12px)",
    CONF_GRID_PAD: "clamp(8px, 0.8vw, 14px)",
    CONF_LAYOUT: DEFAULT_LAYOUT,
    CONF_HIDDEN_WIDGETS: ["metro", "scripture", "todo", "nowplaying", "haalerts"],
    # Enabled small-screen sections; Scripture is off by default.
    CONF_MOBILE_MODULES: [m for m in MOBILE_MODULES if m != "scripture"],
    # Order of every section (enabled or not), so turning one off and on
    # again keeps its place.
    CONF_MOBILE_ORDER: list(MOBILE_MODULES),
    CONF_MOBILE_DURATIONS: DEFAULT_MOBILE_DURATIONS,
    CONF_MOBILE_HIDE_ERRORS: True,
    CONF_REGISTER_PANEL: True,
    CONF_PANEL_TITLE: "Rundown Tweaks",
    CONF_PANEL_ICON: "mdi:view-dashboard-variant",
    CONF_INSTALL_CLOCK_VIEW: False,
    CONF_INSTALL_APP_VIEW: False,
    CONF_SIDEBAR_MODE: "off",
    CONF_SIDEBAR_POSITION: "right",
    CONF_CLOCK_BACKGROUND: "view_assist",
    CONF_CLOCK_THERMOSTAT: True,
}

# Options that are secrets: redacted from diagnostics.
SECRET_KEYS: Final = frozenset(
    {
        CONF_WEATHER_KEY,
        CONF_WMATA_KEY,
        CONF_ICS_URL,
        CONF_GRAPH_TOKEN,
        CONF_ESV_KEY,
        CONF_LASTFM_KEY,
        CONF_MS_CLIENT_SECRET,
        CONF_MS_REFRESH_TOKEN,
    }
)

# RSS feeds the server-side fetch proxy may retrieve, in addition to the
# configured ICS URL and custom ticker feed. Nothing else is fetchable.
BUILTIN_FEEDS: Final[dict[str, tuple[str, str]]] = {
    "wtop": ("WTOP", "https://wtop.com/local/feed/"),
    "san": ("Straight Arrow News", "https://san.com/sa_editorial_type/top-stories/feed/"),
}
FETCH_MAX_BYTES: Final = 2 * 1024 * 1024
FETCH_TIMEOUT: Final = 15

WS_STATUS: Final = f"{DOMAIN}/status"
WS_CONFIG: Final = f"{DOMAIN}/config"
WS_SAVE_LAYOUT: Final = f"{DOMAIN}/save_layout"
WS_SAVE_TODO_TOKEN: Final = f"{DOMAIN}/save_todo_token"
WS_FETCH: Final = f"{DOMAIN}/fetch"

SERVICE_INSTALL_VA_ASSETS: Final = "install_view_assist_assets"
SERVICE_REMOVE_VA_ASSETS: Final = "remove_view_assist_assets"
