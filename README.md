# View Assist Rundown Tweaks

A Home Assistant integration that packages **Rundown** — a glanceable wall
dashboard (clock, weather, agenda, metro, tasks, scripture, now playing, news
ticker, door/broadcast alerts) — together with a matching look for
[View Assist](https://github.com/dinki/view_assist_integration) displays. Other
tweaks are included and available.

## Disclaimers

- The majority of this code has been LLM authored or LLM augmented, chiefly with Claude Sonnet 4.6 and Opus 5.
- The current state of this project should be considered ALPHA - please take caution if/when using this integration on a production Home Assistant instance. Please **backup** before installing!
- Pull requests and issues are welcome!
- A lot of this integration's components were tailored to and built for products/services/configurations that I use in my setup. I'm working to make this more and more modular to support more customization.

## Acknowledgements

- The concept and architecture for Rundown was inspired by [MagicMirror²](https://github.com/magicmirrororg/magicmirror)
- The side bar tweak is largely a fork of [View Assist Side Menu](https://docs.ostat.com/docs/projects/view_assist/) from Chris/ostat, which was also inspired by [The Stock Pot](https://www.youtube.com/watch?v=6p5wvVl957c)
- The [View Assist](https://github.com/dinki/view_assist_integration) and [VACA](https://github.com/msp1974/ViewAssist_Companion_App) projects are vital to these kinds of setups

| Component | Function |
| --- | --- |
| **Rundown dashboard** | The full Rundown page, as a sidebar panel (`/va-rundown-tweaks`), a Lovelace card (`custom:va-rundown-tweaks-card`), and optionally a full-screen View Assist view (`rundown`). Desktop grid layout on large screens, a rotating single-module layout on short screens such as 960×480 tablets. This is determined automatically based on screen size. |
| **Rundown clock view** | A View Assist view (`rundowntweaksclock`) restyled to match the rest of Rundown: IBM Plex type, animated weather icon, thermostat readout, and night-mode dimming. |
| **Sidebar menu** | `custom:view-assist-menu-card`: a floating bar built from each View Assist device's `menu_items` (views, entity toggles, `service:` and `press:` items). Can be added to the Rundown clock view only, or to every View Assist view. Fork of [View Assist Side Menu](https://docs.ostat.com/docs/projects/view_assist/) from Chris/ostat, which was also inspired by [The Stock Pot](https://www.youtube.com/watch?v=6p5wvVl957c) |
| **Weather sky background** | An animated WebGL sky (sun/moon position, moon phase, clouds, rain, snow, fog, lightning) driven by any Home Assistant weather entity. Use it as the clock view background, or as any View Assist device background. |

Everything is configured in **Settings → Devices & services → View Assist
Rundown → Configure**.

## Requirements

- Home Assistant 2025.10 or newer.
- For the View Assist pieces: View Assist, with its master configuration and
  dashboard set up, plus [button-card](https://github.com/custom-cards/button-card)
  (already required by View Assist).
- The Rundown dashboard itself does not need View Assist.

## Installation

**HACS:** add this repository as a custom repository (type *Integration*),
install **View Assist Rundown Tweaks**, and restart Home Assistant.

**Manual:** copy `custom_components/va_rundown_tweaks` into your
`config/custom_components/` folder and restart Home Assistant.

Then go to **Settings → Devices & services → Add integration → View Assist
Rundown**. You can:

- **Start fresh.** Pick a weather entity, units and clock format; everything
  else is under *Configure*.
- **Import an existing `rundown-config.json`.** This is mostly used for testing.

## Configuration

*Configure* opens a menu. Edit any section, then choose **Save**. Open Rundown
screens reload with the new settings within a minute. When in sub-menus, make sure
to navigate back out to the main menu and save before closing.

| Section | Options |
| --- | --- |
| Display | Text size, text shadow, 24-hour clock, US/metric units, compact-layout height, IBM Plex fonts |
| Background photos | Folder inside your config directory, optional explicit list (file names or URLs), shuffle, seconds per photo |
| Weather | Source (Home Assistant weather entity *or* Pirate Weather API), location, forecast rotation slides and timings, broadcast-style layout and city name |
| News ticker | WTOP (Washington DC), Straight Arrow News or a custom RSS feed; speed, height; optional public CORS-proxy fallback |
| Calendar | ICS/webcal URL, or a Microsoft Graph `calendarView` URL + token |
| Tasks | Any Home Assistant to-do lists (defaults to all Todoist lists), or Microsoft To Do; date window; undated tasks |
| Metro (WMATA) | API key and station codes for Washington DC's metro transit system. Support for other systems coming soon |
| Scripture | ESV API key (without one, a built-in verse rotation is shown) |
| Now playing | Last.fm API key and username, future support planned for Music Assistant |
| Home Assistant alerts | Door sensor + "opened by" entity, broadcast text entity and duration, thermostat |
| Content → Full screen | Grid size/gap/padding; for each widget: show, column, row, width, height |
| Content → Small screen | Hide sections with errors; for each section: show, position in the rotation, seconds on screen (Weather and HA alerts: 0 = automatic) |
| View Assist & sidebar panel | Configure how Rundown interacts with View Assist, including sidebar panel title/icon, full-screen Rundown view (`rundowntweaks`), Rundown clock view (`rundowntweaksclock`), clock background (device background or animated sky), thermostat on clock, sidebar menu (off / clock view / all views) and side |

**Layout editing on the page:** as a Home Assistant admin, tap the RUNDOWN
logo five times to open the layout editor. You can drag and resize panels,
add and remove widgets, and reorder the weather slides (⚙ on the weather
panel). Changes save to the integration automatically. *Settings* in that
toolbar jumps to the options above.

### Quick start

After the initial configuration, set `/view-assist/rundowntweaks` or 
`/view-assist/rundowntweaksclock` to a device's home view in View Assist.

### Weather sky as a View Assist background

Choose *Animated weather sky* as the clock view background. Alternatively,
set any View Assist device's background to `/va_rundown_tweaks/static/sky.html`: the
Rundown clock view shows `.html` backgrounds as a live page. The sky follows
the device's own weather entity; `?weather=weather.other` overrides it.

### View Assist views

**Full-screen Rundown.** *Add full-screen Rundown as a View Assist view*
adds a `rundowntweaks` view that fills the whole screen, above the Home Assistant
header and sidebar, whatever the device's View Assist screen mode. You can
open it with `view_assist.navigate` (path `/view-assist/rundowntweaks`), add
`view:rundowntweaks` to a device's menu items, or **make it the device's home screen**.
Like any other non-home View Assist view, it returns to the home screen after
the device's view timeout unless the device is in hold mode.

**Rundown clock.** With *Install the Rundown clock view* enabled, the
integration writes `config/view_assist/views/rundowntweaksclock/rundowntweaksclock.yaml`
and adds it to the View Assist dashboard the same way View Assist installs its
own views. To use it as a device's home screen, set that
device's home view to `/view-assist/rundowntweaksclock` in View Assist. To customise
the view, copy the file to `user_rundowntweaksclock.yaml` in the same folder; View
Assist prefers the `user_` copy. The same applies to the `rundowntweaks` view.

The *all views* sidebar is added as one extra button-card template
(`rundown_tweaks_navbar_overlay`) on the View Assist dashboard. It is skipped if the
dashboard already adds a `view-assist-menu-card` some other way.

Actions: `va_rundown_tweaks.install_view_assist_assets` (re-apply, optionally forced)
and `va_rundown_tweaks.remove_view_assist_assets`.

### Disabling and removing

**Disabling** the integration suspends all of Rundown and all tweaks
- The sidebar panel and its actions are removed.
- Its dashboard resources, View Assist views and sidebar template are
  withdrawn.
- The Rundown and sky pages are no longer served; open screens switch to a
  "disabled" page within a minute.
- Its websocket API and photo view refuse requests.

If a View Assist device uses `rundowntweaksclock` or `rundowntweaks` as its home screen,
point it back at `clock` before disabling. **Enabling** it again reinstalls
everything from the saved options. **Deleting** the integration removes the
same pieces.

### Microsoft To Do

Register an Azure app as a **single-page application** with redirect URI
`https://<your-home-assistant>/va_rundown_tweaks/static/rundown.html`. Enter its
Client ID under *Tasks → Microsoft To Do*, then use **Link Microsoft** in the
page's layout editor. The refresh token is stored in the integration and kept
current as Microsoft rotates it.

## How it signs in (security model)

Rundown pages always run inside Home Assistant: the panel, the card or a View
Assist view. The page uses the viewing user's existing Home Assistant session
rather than a stored long-lived token.

- Entity states come from the frontend's live connection. To-do items and
  forecasts are fetched with that user's permissions.
- Settings are delivered over an authenticated websocket command. The layout
  editor can only save as an admin.
- Background photos are served by an authenticated view using signed URLs, so
  they are never public.
- The calendar and ticker feeds are fetched by Home Assistant itself, by
  source name only. The private ICS link never reaches the browser, and the
  fetcher cannot be used as an open proxy. Public CORS proxies are used only
  if you enable the fallback.
- Keys for services the browser calls directly (Pirate Weather, WMATA, ESV,
  Last.fm, Microsoft Graph) are sent to signed-in Home Assistant users.

## Development

`rundown_config.py` (options ↔ page config, legacy import) has no Home
Assistant imports and can be tested on its own. Bump `FRONTEND_VERSION` in
`const.py` whenever anything under `www/` changes, so browsers pick up the new
files.
