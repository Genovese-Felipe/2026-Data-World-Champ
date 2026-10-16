# Architecture

How the COSMOS app fits together. Every module is a defensive IIFE that attaches its public API to `window`, loads in a specific order via `<script>` tags in `index.html`, and has **no build step**.

```
index.html
   │
   ├── three.js + OrbitControls  (CDN, the only external dep)
   │
   ├── js/i18n.js      → window.I18n          (10-language switcher)
   ├── js/nasa.js      → window.NASA          (API client + cache + fallbacks)
   ├── js/audio.js     → window.COSMOS_AUDIO  (procedural sound)
   ├── js/scene.js     → window.COSMOS_SCENE  (three.js solar system)
   ├── js/export.js    → window.COSMOS_EXPORT (image/video capture)
   ├── js/panels.js    → window.COSMOS_PANELS (6 NASA data panels)
   └── js/app.js       → window.COSMOS_APP    (controller — wires it all)
```

## Load order matters

`app.js` is last and auto-boots on `DOMContentLoaded`. It depends on all the others being present. The sequence in `index.html`:

1. **three.js** (CDN) — defines `window.THREE`.
2. **i18n.js** — pure data + lookup, no deps.
3. **nasa.js** — pure fetch/cache, no deps.
4. **audio.js** — uses `window.AudioContext`, no deps on other modules.
5. **scene.js** — uses `window.THREE` (must come after three.js).
6. **export.js** — uses `window.COSMOS_SCENE` at call-time (not load-time), so order vs scene.js is flexible.
7. **panels.js** — uses `window.NASA` and `window.I18n` at call-time.
8. **app.js** — orchestrator; calls into every module.

## The boot sequence (`app.js`)

```
DOMContentLoaded
   └─ waitForThree()              (polls until THREE is on window)
      └─ APP.init()
         ├─ I18n.apply(document)         (translate static strings)
         ├─ initNav()                    (panel switching)
         ├─ initSettings()               (drawer: API key, language, cache)
         ├─ initToggles()                (quality + sound + orbit buttons)
         ├─ initExport()                 (format/res selectors + buttons)
         ├─ initKeyboard()                (1-7, S, O, P shortcuts)
         ├─ initAudioUnlock()             (one-gesture autoplay unlock)
         └─ loadingRitual() ──┐
                              │  (2s progress bar)
                              ▼
                      COSMOS_SCENE.init()   (build three.js scene)
                      showPanel("explore")  (reveal scene)
```

## Data flow: a NASA panel

```
User clicks "Mars Rovers" (nav)
   └─ app.showPanel("mars")
      └─ panels.renderMars(rootEl)
         └─ NASA.marsRovers()           → fetch cached? else fetch + cache
            └─ NASA.marsPhotos(rover,sol)
               └─ fetchJSON(url, key, fallback)
                  ├─ cache hit?      → {data, cached:true,  sample:false}
                  ├─ fetch ok?       → {data, cached:false, sample:false} + write cache
                  └─ fetch fails?    → {data:fallback, sample:true}   (UI never empty)
         └─ render DOM into rootEl
            └─ statusBadge(res)        → LIVE / cached / SAMPLE
```

## Caching strategy (`nasa.js`)

- Every `fetchJSON(url, cacheKey, fallback)` checks `localStorage["cosmos.cache."+key]` first.
- Cache entries carry a 6-hour TTL (`exp` field). On read, expired entries are purged.
- On network failure, an **expired** cache entry is still returned (marked `stale`) before falling back to the bundled sample — so a previously-seen live result beats a synthetic sample.
- `NASA.clearCache()` wipes all `cosmos.cache.*` keys (used by the Settings "Clear cache" button and on API-key change).

## Quality presets (`scene.js`)

`setQuality(key)` disposes and rebuilds the entire three.js scene at the new fidelity. Presets scale: device-pixel-ratio cap, star count, sphere segment counts, shadow-map size, and whether shadows are enabled at all. The choice persists in `localStorage["cosmos.quality"]`.

## Export pipeline (`export.js`)

### Image
`COSMOS_EXPORT.image(format, w, h)` calls `COSMOS_SCENE.getScreenshot(w, h)`, which temporarily resizes the renderer's drawing buffer to the target resolution, renders one frame, captures `canvas.toDataURL()`, and restores the original size. For JPEG, the PNG dataURL is re-encoded onto a canvas at quality 0.92. Resolutions up to 8K (7680×4320) are clamped for safety.

### Video
`startVideo(fps)` calls `renderer.domElement.captureStream(fps)` and feeds it to `MediaRecorder`, picking the best-supported MIME type (VP9 → VP8 → WebM → MP4). `stopVideo()` finalizes a Blob and triggers a download. Recording works on the live animation loop, so orbit/auto-orbit movements are captured.

## Internationalization (`i18n.js`)

- Flat dotted keys (`"nav.apod"`, `"status.live"`, …) in a single `STRINGS` object, one sub-object per key with a value per language code.
- `I18n.t(key, vars)` interpolates `{name}` placeholders.
- `I18n.apply(root)` walks the DOM for `data-i18n` (textContent) and `data-i18n-attr` (attribute) markers and translates them in place — called on boot and on every `langchange`.
- `I18n.set(code)` persists the choice, sets `<html lang>` and `dir` (RTL for Arabic), dispatches `langchange`, and re-applies. Dynamic panels re-render themselves on `langchange` via `COSMOS_APP.reloadActivePanel()`.
