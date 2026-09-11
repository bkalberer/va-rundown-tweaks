"""Translate between config-entry options and the Rundown page config.

Kept free of Home Assistant imports so it can be unit tested on its own.
The page itself still speaks the camelCase shape rundown.html has always
used, so its merge/apply logic did not have to change.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
import copy
import hashlib
import json
from pathlib import PurePosixPath
from typing import Any
from urllib.parse import quote

from .const import (
    BUILTIN_FEEDS,
    CONF_BG_FOLDER,
    CONF_BG_IMAGES,
    CONF_BG_INTERVAL,
    CONF_BG_SHUFFLE,
    CONF_BROADCAST_ENTITY,
    CONF_BROADCAST_SECONDS,
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
    CONF_WX_SLIDE_ORDER,
    CONF_WX_SLIDE_TIMES,
    CONF_WX_SLIDES_ENABLED,
    DEFAULT_LAYOUT,
    DEFAULT_MOBILE_DURATIONS,
    DEFAULT_WX_SLIDE_TIMES,
    DEFAULTS,
    FRONTEND_VERSION,
    MOBILE_MODULES,
    PHOTO_URL,
    TEXT_SCALES,
    WIDGETS,
    WX_SLIDES,
)

# Keys the page can change without the integration having to reload
# (layout editor, weather-rotation editor, Microsoft token refresh).
PAGE_ONLY_KEYS = frozenset(
    {
        CONF_LAYOUT,
        CONF_HIDDEN_WIDGETS,
        CONF_TICKER_HEIGHT,
        CONF_WX_ROTATION,
        CONF_WX_SLIDE_ORDER,
        CONF_WX_SLIDES_ENABLED,
        CONF_WX_SLIDE_TIMES,
        CONF_MS_REFRESH_TOKEN,
    }
)


def merged_options(options: Mapping[str, Any]) -> dict[str, Any]:
    """Return defaults overlaid with the stored options."""
    out = copy.deepcopy(DEFAULTS)
    for key, value in options.items():
        out[key] = copy.deepcopy(value)
    # Entries saved before the small-screen order option existed kept their
    # order inside mobile_modules; carry that over rather than the default.
    if not options.get(CONF_MOBILE_ORDER) and options.get(CONF_MOBILE_MODULES):
        out[CONF_MOBILE_ORDER] = list(options[CONF_MOBILE_MODULES])
    out[CONF_MOBILE_ORDER] = mobile_order(out[CONF_MOBILE_ORDER])
    return out


def mobile_order(values: Iterable[Any] | None) -> list[str]:
    """Every small-screen section exactly once: the given order, then the rest."""
    order = _ordered_known(values or [], MOBILE_MODULES)
    return order + [m for m in MOBILE_MODULES if m not in order]


def reorder_by_positions(order: list[str], positions: Mapping[str, int]) -> list[str]:
    """Apply position numbers (1-based) typed into the small-screen form.

    Sections whose number did not change keep their relative order; each
    section given a new number is then taken out and inserted at that
    position, so "move Clock from 1 to 3" puts Clock third, not second.
    """
    order = mobile_order(order)
    current = {m: i + 1 for i, m in enumerate(order)}
    moved = [m for m in order if int(positions.get(m, current[m])) != current[m]]
    result = [m for m in order if m not in moved]
    for module in sorted(moved, key=lambda m: (int(positions[m]), current[m])):
        index = max(0, min(len(result), int(positions[module]) - 1))
        result.insert(index, module)
    return result


def split_lines(text: Any) -> list[str]:
    """Split a multi-line text option into non-empty stripped lines."""
    return [line.strip() for line in str(text or "").splitlines() if line.strip()]


def split_csv(text: Any) -> list[str]:
    """Split a comma separated option into non-empty stripped values."""
    return [item.strip() for item in str(text or "").split(",") if item.strip()]


def normalize_url(url: Any) -> str:
    """Trim a URL and turn webcal:// into https://."""
    url = str(url or "").strip()
    if url.lower().startswith("webcal:"):
        url = "https:" + url[len("webcal:") :]
    return url


def is_http_url(url: str) -> bool:
    """Return True for absolute http(s) URLs."""
    return url.lower().startswith(("http://", "https://"))


def sanitize_layout(layout: Any) -> dict[str, dict[str, int]]:
    """Keep only known widgets with four integer grid coordinates."""
    out = copy.deepcopy(DEFAULT_LAYOUT)
    if not isinstance(layout, Mapping):
        return out
    for widget, pos in layout.items():
        if widget not in WIDGETS or not isinstance(pos, Mapping):
            continue
        try:
            cells = {key: int(pos[key]) for key in ("cs", "ce", "rs", "re")}
        except (KeyError, TypeError, ValueError):
            continue
        if cells["ce"] > cells["cs"] and cells["re"] > cells["rs"] and min(cells.values()) >= 1:
            out[widget] = cells
    return out


def _ordered_known(values: Iterable[Any], known: Iterable[str]) -> list[str]:
    known = list(known)
    seen: list[str] = []
    for value in values or []:
        if value in known and value not in seen:
            seen.append(value)
    return seen


def wx_slides(opts: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Build the page's ordered weather-slide list."""
    order = _ordered_known(opts.get(CONF_WX_SLIDE_ORDER), WX_SLIDES)
    order += [slide for slide in WX_SLIDES if slide not in order]
    enabled = set(opts.get(CONF_WX_SLIDES_ENABLED) or [])
    times = {**DEFAULT_WX_SLIDE_TIMES, **(opts.get(CONF_WX_SLIDE_TIMES) or {})}
    return [
        {
            "id": slide,
            "label": WX_SLIDES[slide],
            "enabled": slide in enabled,
            "time": max(1, int(times.get(slide) or DEFAULT_WX_SLIDE_TIMES[slide])),
        }
        for slide in order
    ]


def ticker_feeds(opts: Mapping[str, Any]) -> dict[str, dict[str, str]]:
    """Return the ticker feeds the page may request, by id (no URLs)."""
    feeds = {key: {"label": label} for key, (label, _url) in BUILTIN_FEEDS.items()}
    if is_http_url(normalize_url(opts.get(CONF_TICKER_CUSTOM_URL))):
        feeds["custom"] = {"label": str(opts.get(CONF_TICKER_CUSTOM_LABEL) or "News")}
    return feeds


def fetch_url_for_source(opts: Mapping[str, Any], source: str) -> str | None:
    """Resolve a fetch-proxy source id to the only URL it may fetch."""
    if source == "ics":
        url = normalize_url(opts.get(CONF_ICS_URL))
    elif source == "custom":
        url = normalize_url(opts.get(CONF_TICKER_CUSTOM_URL))
    elif source in BUILTIN_FEEDS:
        url = BUILTIN_FEEDS[source][1]
    else:
        return None
    return url if is_http_url(url) else None


def photo_urls(opts: Mapping[str, Any], folder_files: list[str]) -> list[str]:
    """Return background image URLs for the page.

    An explicit list wins (keeps a curated order); otherwise every image in the
    configured folder is used. Folder images are served by the authenticated
    photo view, so the page signs each URL before displaying it.
    """
    explicit = split_lines(opts.get(CONF_BG_IMAGES))
    if not explicit:
        return [f"{PHOTO_URL}/{quote(name)}" for name in folder_files]
    urls = []
    for item in explicit:
        if is_http_url(item) or item.startswith("/"):
            urls.append(item)
        elif opts.get(CONF_BG_FOLDER):
            urls.append(f"{PHOTO_URL}/{quote(PurePosixPath(item).name)}")
    return urls


def nearest_text_scale(value: Any) -> str:
    """Map any numeric text scale onto one of the offered choices."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "1"
    return min(TEXT_SCALES, key=lambda choice: abs(float(choice) - number))


def build_page_config(
    options: Mapping[str, Any],
    *,
    photos: list[str],
    is_admin: bool,
    default_lat: float | None,
    default_lon: float | None,
) -> dict[str, Any]:
    """Build the object rundown.html consumes."""
    o = merged_options(options)
    lat = o.get(CONF_LATITUDE)
    lon = o.get(CONF_LONGITUDE)
    proxy_fallback = bool(o[CONF_CORS_PROXY_FALLBACK])

    cfg: dict[str, Any] = {
        "version": FRONTEND_VERSION,
        "isAdmin": is_admin,
        # Background
        "bgImages": photos,
        "bgLocalPath": "",
        "bgInterval": int(o[CONF_BG_INTERVAL]),
        "bgShuffle": bool(o[CONF_BG_SHUFFLE]),
        # Display
        "textScale": float(o[CONF_TEXT_SCALE]),
        "textShadowEnabled": bool(o[CONF_TEXT_SHADOW]),
        "use24h": bool(o[CONF_USE_24H]),
        "units": o[CONF_UNITS],
        "mobileBreakpoint": int(o[CONF_MOBILE_BREAKPOINT]),
        "loadFonts": bool(o[CONF_LOAD_FONTS]),
        # Weather
        "weatherSource": o[CONF_WEATHER_SOURCE],
        "weatherKey": o[CONF_WEATHER_KEY],
        "weatherEntity": o[CONF_WEATHER_ENTITY],
        "lat": float(lat if lat is not None else (default_lat or 0.0)),
        "lon": float(lon if lon is not None else (default_lon or 0.0)),
        "wxRotationEnabled": bool(o[CONF_WX_ROTATION]),
        "wxSlides": wx_slides(o),
        "wxIntelliStar": bool(o[CONF_WX_BROADCAST_STYLE]),
        "wxCityName": o[CONF_WX_CITY_NAME],
        # Ticker
        "tickerPrimarySource": o[CONF_TICKER_SOURCE],
        "tickerFeeds": ticker_feeds(o),
        "tickerSpeed": float(o[CONF_TICKER_SPEED]),
        "tickerHeight": o[CONF_TICKER_HEIGHT],
        "corsProxyFallback": proxy_fallback,
        # Transit
        "wmataKey": o[CONF_WMATA_KEY],
        "stations": split_csv(o[CONF_WMATA_STATIONS]),
        # Calendar. The ICS URL usually embeds a private token, so it is
        # only handed to the browser when public CORS proxies are allowed;
        # otherwise Home Assistant fetches it server-side by source id.
        "icsConfigured": bool(fetch_url_for_source(o, "ics")),
        "icsUrl": normalize_url(o[CONF_ICS_URL]) if proxy_fallback else "",
        "outlookUrl": o[CONF_GRAPH_URL],
        "outlookToken": o[CONF_GRAPH_TOKEN],
        # Scripture / music
        "esvKey": o[CONF_ESV_KEY],
        "lfmKey": o[CONF_LASTFM_KEY],
        "lfmUser": o[CONF_LASTFM_USER],
        # Tasks
        "todoSource": o[CONF_TODO_SOURCE],
        "todoEntities": list(o[CONF_TODO_ENTITIES] or []),
        "todoistListName": o[CONF_TODO_FILTER],
        "todoOverdueDays": int(o[CONF_TODO_OVERDUE_DAYS]),
        "todoFutureDays": int(o[CONF_TODO_FUTURE_DAYS]),
        "todoShowUndated": bool(o[CONF_TODO_SHOW_UNDATED]),
        "todoClientId": o[CONF_MS_CLIENT_ID],
        "todoClientSecret": o[CONF_MS_CLIENT_SECRET],
        "todoRefreshToken": o[CONF_MS_REFRESH_TOKEN],
        "todoListName": o[CONF_MS_LIST_NAME],
        # HA alerts / readouts
        "haFrontDoorEntity": o[CONF_DOOR_ENTITY],
        "haFrontDoorOperatorEntity": o[CONF_DOOR_OPERATOR_ENTITY],
        "haBroadcastEntity": o[CONF_BROADCAST_ENTITY],
        "broadcastSeconds": int(o[CONF_BROADCAST_SECONDS]),
        "haThermostatEntity": o[CONF_THERMOSTAT_ENTITY],
        # Layout
        "gridCols": int(o[CONF_GRID_COLS]),
        "gridRows": int(o[CONF_GRID_ROWS]),
        "gridGap": str(o[CONF_GRID_GAP]),
        "gridPad": str(o[CONF_GRID_PAD]),
        "layout": sanitize_layout(o[CONF_LAYOUT]),
        "hiddenWidgets": _ordered_known(o[CONF_HIDDEN_WIDGETS], WIDGETS),
        # Enabled sections, in the configured order.
        "mobileModules": [m for m in o[CONF_MOBILE_ORDER] if m in set(o[CONF_MOBILE_MODULES] or [])],
        "mobileDurations": {
            **DEFAULT_MOBILE_DURATIONS,
            **{
                key: max(0, int(value))
                for key, value in (o[CONF_MOBILE_DURATIONS] or {}).items()
                if key in MOBILE_MODULES
            },
        },
        "mobileHideErrors": bool(o[CONF_MOBILE_HIDE_ERRORS]),
    }
    cfg["configHash"] = config_hash(cfg)
    return cfg


def config_hash(cfg: Mapping[str, Any]) -> str:
    """Short stable hash the page polls to notice option changes."""
    payload = {k: v for k, v in cfg.items() if k not in ("configHash", "isAdmin")}
    return hashlib.sha1(
        json.dumps(payload, sort_keys=True, default=str).encode()
    ).hexdigest()[:12]


def options_from_page_layout(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Convert a layout/weather-rotation save from the page into options."""
    out: dict[str, Any] = {}
    if "layout" in payload:
        out[CONF_LAYOUT] = sanitize_layout(payload["layout"])
    if "hidden_widgets" in payload:
        out[CONF_HIDDEN_WIDGETS] = _ordered_known(payload["hidden_widgets"], WIDGETS)
    if "ticker_height" in payload:
        height = payload["ticker_height"]
        out[CONF_TICKER_HEIGHT] = None if height is None else max(20, int(height))
    if "wx_rotation_enabled" in payload:
        out[CONF_WX_ROTATION] = bool(payload["wx_rotation_enabled"])
    if "wx_slides" in payload:
        slides = [s for s in payload["wx_slides"] if isinstance(s, Mapping)]
        out[CONF_WX_SLIDE_ORDER] = _ordered_known((s.get("id") for s in slides), WX_SLIDES)
        out[CONF_WX_SLIDES_ENABLED] = _ordered_known(
            (s.get("id") for s in slides if s.get("enabled")), WX_SLIDES
        )
        out[CONF_WX_SLIDE_TIMES] = {
            s["id"]: max(1, int(s.get("time") or 1)) for s in slides if s.get("id") in WX_SLIDES
        }
    return out


def _legacy_folder(local_path: str, legacy_base: str) -> str:
    """Turn rundown-config.json's bgLocalPath into a config-dir relative folder."""
    path = str(local_path or "").strip()
    if not path:
        return ""
    if path.startswith("/local/"):
        return str(PurePosixPath("www", path[len("/local/") :]))
    if path.startswith("/") or is_http_url(path):
        return ""
    return str(PurePosixPath(legacy_base, path))


def options_from_legacy(data: Mapping[str, Any], legacy_base: str = "www/rundown") -> dict[str, Any]:
    """Map a standalone rundown-config.json onto integration options.

    legacy_base is the folder rundown.html lived in, relative to the config
    dir, used to resolve a relative bgLocalPath. The standalone haToken is
    intentionally not imported: the integration authenticates as the viewing
    Home Assistant user instead of a stored long-lived token.
    """
    out: dict[str, Any] = {}

    def put(key: str, legacy: str, convert=lambda v: v) -> None:
        if data.get(legacy) is not None:
            out[key] = convert(data[legacy])

    folder = _legacy_folder(data.get("bgLocalPath", ""), legacy_base)
    if folder:
        out[CONF_BG_FOLDER] = folder
    images = [str(i) for i in data.get("bgImages") or [] if not str(i).startswith("blob:")]
    if images:
        out[CONF_BG_IMAGES] = "\n".join(images)
    put(CONF_BG_INTERVAL, "bgInterval", int)

    if data.get("weatherKey"):
        out[CONF_WEATHER_SOURCE] = "pirateweather"
        out[CONF_WEATHER_KEY] = data["weatherKey"]
    put(CONF_LATITUDE, "lat", float)
    put(CONF_LONGITUDE, "lon", float)
    put(CONF_WX_ROTATION, "wxRotationEnabled", bool)
    if isinstance(data.get("wxSlides"), list):
        out.update(options_from_page_layout({"wx_slides": data["wxSlides"]}))
    put(CONF_WX_BROADCAST_STYLE, "wxIntelliStar", bool)
    put(CONF_WX_CITY_NAME, "wxCityName", str)

    if data.get("tickerPrimarySource") in ("wtop", "san"):
        out[CONF_TICKER_SOURCE] = data["tickerPrimarySource"]
    put(CONF_TICKER_SPEED, "tickerSpeed", float)
    put(CONF_TICKER_HEIGHT, "tickerHeight", int)

    put(CONF_WMATA_KEY, "wmataKey", str)
    if isinstance(data.get("stations"), list):
        out[CONF_WMATA_STATIONS] = ",".join(str(s) for s in data["stations"])
    put(CONF_ICS_URL, "icsUrl", str)
    put(CONF_GRAPH_URL, "outlookUrl", str)
    put(CONF_GRAPH_TOKEN, "outlookToken", str)
    put(CONF_ESV_KEY, "esvKey", str)
    put(CONF_LASTFM_KEY, "lfmKey", str)
    put(CONF_LASTFM_USER, "lfmUser", str)

    if data.get("haToken"):
        out[CONF_TODO_SOURCE] = "home_assistant"
    elif data.get("todoClientId") and data.get("todoRefreshToken"):
        out[CONF_TODO_SOURCE] = "microsoft"
    put(CONF_TODO_FILTER, "todoistListName", str)
    put(CONF_TODO_OVERDUE_DAYS, "todoOverdueDays", int)
    put(CONF_TODO_FUTURE_DAYS, "todoFutureDays", int)
    put(CONF_TODO_SHOW_UNDATED, "todoShowUndated", bool)
    put(CONF_MS_CLIENT_ID, "todoClientId", str)
    put(CONF_MS_CLIENT_SECRET, "todoClientSecret", str)
    put(CONF_MS_REFRESH_TOKEN, "todoRefreshToken", str)
    put(CONF_MS_LIST_NAME, "todoListName", str)

    put(CONF_DOOR_ENTITY, "haFrontDoorEntity", str)
    put(CONF_DOOR_OPERATOR_ENTITY, "haFrontDoorOperatorEntity", str)
    put(CONF_BROADCAST_ENTITY, "haBroadcastEntity", str)
    put(CONF_THERMOSTAT_ENTITY, "haThermostatEntity", str)

    put(CONF_TEXT_SCALE, "textScale", nearest_text_scale)
    put(CONF_TEXT_SHADOW, "textShadowEnabled", bool)

    put(CONF_GRID_COLS, "gridCols", int)
    put(CONF_GRID_ROWS, "gridRows", int)
    put(CONF_GRID_GAP, "gridGap", str)
    put(CONF_GRID_PAD, "gridPad", str)
    if isinstance(data.get("layout"), Mapping):
        out[CONF_LAYOUT] = sanitize_layout(data["layout"])
    if isinstance(data.get("hiddenWidgets"), list):
        out[CONF_HIDDEN_WIDGETS] = _ordered_known(data["hiddenWidgets"], WIDGETS)
    if isinstance(data.get("mobileModules"), list):
        out[CONF_MOBILE_MODULES] = _ordered_known(data["mobileModules"], MOBILE_MODULES)
        out[CONF_MOBILE_ORDER] = mobile_order(data["mobileModules"])
    if isinstance(data.get("mobileDurations"), Mapping):
        out[CONF_MOBILE_DURATIONS] = {
            k: int(v) for k, v in data["mobileDurations"].items() if k in MOBILE_MODULES
        }
    return out
