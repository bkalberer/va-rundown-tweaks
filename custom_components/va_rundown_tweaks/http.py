"""Authenticated photo serving for the Rundown background slideshow."""

from __future__ import annotations

from http import HTTPStatus
from pathlib import Path

from aiohttp import web

from homeassistant.components.http import HomeAssistantView
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers.http import KEY_HASS

from .const import CONF_BG_FOLDER, DOMAIN, IMAGE_EXTENSIONS, PHOTO_URL, STATIC_URL

WWW_DIR = Path(__file__).parent / "www"
DISABLED_PAGE = (
    "<!doctype html><meta charset='utf-8'><title>Rundown</title>"
    "<body style='margin:0;height:100vh;display:flex;align-items:center;justify-content:center;"
    "background:#080909;color:#9199a6;font:14px sans-serif'>View Assist Rundown Tweaks is disabled.</body>"
)


def _is_loaded(hass: HomeAssistant) -> bool:
    return any(
        entry.state is ConfigEntryState.LOADED
        for entry in hass.config_entries.async_entries(DOMAIN)
    )


class RundownStaticView(HomeAssistantView):
    """Serve the Rundown page, sky page and card modules from www/.

    A view rather than a static path so it can refuse to serve anything
    while the integration is disabled or not loaded (a static path cannot be
    unregistered once added). Unauthenticated because Lovelace loads module
    resources and iframes without an Authorization header; these files hold
    no configuration or secrets.
    """

    url = STATIC_URL + "/{filename}"
    name = f"{DOMAIN}:static"
    requires_auth = False

    async def get(self, request: web.Request, filename: str) -> web.StreamResponse:
        """Return one frontend file."""
        hass = request.app[KEY_HASS]
        if not _is_loaded(hass):
            if filename.endswith(".html"):
                return web.Response(
                    status=HTTPStatus.NOT_FOUND, text=DISABLED_PAGE, content_type="text/html"
                )
            return web.Response(status=HTTPStatus.NOT_FOUND)
        if Path(filename).name != filename or filename.startswith("."):
            return web.Response(status=HTTPStatus.NOT_FOUND)
        path = WWW_DIR / filename
        if not await hass.async_add_executor_job(path.is_file):
            return web.Response(status=HTTPStatus.NOT_FOUND)
        # no-cache = revalidate each time, so disabling takes effect at once
        # and updated files are picked up without a hard refresh.
        return web.FileResponse(path, headers={"Cache-Control": "no-cache"})


def resolve_photo_folder(hass: HomeAssistant, relative: str | None) -> Path | None:
    """Resolve a config-dir relative folder, refusing anything outside it."""
    if not relative:
        return None
    base = Path(hass.config.config_dir).resolve()
    folder = (base / relative).resolve()
    if not folder.is_relative_to(base) or not folder.is_dir():
        return None
    return folder


def list_photos(folder: Path | None) -> list[str]:
    """Return image file names in a folder, sorted (runs in executor)."""
    if folder is None:
        return []
    return sorted(
        entry.name
        for entry in folder.iterdir()
        if entry.is_file() and entry.suffix.lower() in IMAGE_EXTENSIONS
    )


class RundownPhotoView(HomeAssistantView):
    """Serve images from the configured background folder.

    requires_auth stays True: the page requests a signed path through the
    auth/sign_path websocket command (CSS background images cannot carry a
    bearer header), so photos are never publicly readable the way files
    under /local are.
    """

    url = PHOTO_URL + "/{filename}"
    name = f"api:{DOMAIN}:photo"
    requires_auth = True

    async def get(self, request: web.Request, filename: str) -> web.StreamResponse:
        """Return one photo."""
        hass = request.app[KEY_HASS]
        entry = next(
            (
                e
                for e in hass.config_entries.async_entries(DOMAIN)
                if e.state is ConfigEntryState.LOADED
            ),
            None,
        )
        if entry is None:
            return web.Response(status=HTTPStatus.NOT_FOUND)

        folder = await hass.async_add_executor_job(
            resolve_photo_folder, hass, entry.options.get(CONF_BG_FOLDER)
        )
        if folder is None or Path(filename).name != filename:
            return web.Response(status=HTTPStatus.NOT_FOUND)

        path = folder / filename
        if path.suffix.lower() not in IMAGE_EXTENSIONS or not await hass.async_add_executor_job(
            path.is_file
        ):
            return web.Response(status=HTTPStatus.NOT_FOUND)

        return web.FileResponse(path, headers={"Cache-Control": "private, max-age=86400"})
