# 🌌 COSMOS — NASA Open Data Explorer

> An interactive, multilingual explorer for NASA's open data: a **live, ray-traced-lit 3D solar system** you can orbit, plus live data panels for the Astronomy Picture of the Day, Mars rover photos, near-Earth asteroids, Earth imagery, space weather, and NASA spinoffs — with **image export up to 8K** and **video recording**, all running in your browser with no build step.

Built entirely on NASA's public APIs ([api.nasa.gov](https://api.nasa.gov)). Data © NASA. For exploration and education.

---

## ✨ Features at a glance

| Pillar | What you get |
|---|---|
| **3D Solar System** | A real-time three.js scene: procedurally-textured planets, a shader-driven Sun with a noise-based corona + additive glow, Saturn's banded ring system, Earth's moon, a 6,000-star field. Drag to orbit, scroll to zoom, click any body to fly to it. |
| **Live NASA data** | 6 endpoint families, fetched client-side with the shared `DEMO_KEY`, cached 6h in `localStorage`, and gracefully degraded to bundled sample payloads so the UI is never empty. Status badges show **LIVE / cached / SAMPLE** on every panel. |
| **Graphics & "ray tracing"** | Real-time physically-based surface lighting from a moving Sun point-light (diffuse + specular + fresnel rim), plus a fragment-shader Sun built from 5-octave fractal Brownian motion noise — the same families of techniques taught by *Ray Tracing in One Weekend* (Peter Shirley), The Cherno, and Scratchapixel. See [`docs/RAY_TRACING.md`](docs/RAY_TRACING.md). |
| **Sound** | A procedural WebAudio ambient drone (detuned oscillators + filter sweep + LFO) and UI sound effects — all synthesized at runtime, **zero audio files**, fully toggleable. |
| **Navigation & orbit mode** | Mouse drag-orbit / scroll-zoom / right-drag pan, touch support, keyboard shortcuts (1–7 for panels, S sound, O orbit, P screenshot), and a cinematic auto-orbit toggle. |
| **Image quality tuning** | High / Medium / Low presets that scale device-pixel-ratio, star count, and shadow-map size — from phones to 8K workstations. |
| **Image & video export** | Export PNG/JPEG at 1080p, 1440p, 4K, or 8K (offscreen re-render at target resolution); record the live animation as WebM (or MP4 where supported) via `MediaRecorder`. |
| **10 languages** | English · 中文 · Português · Español · 한국어 · Français · Deutsch · 日本語 · العربية · Русский — live switcher, persisted, with RTL support for Arabic. |

---

## 🚀 Quick start

**No build step. No dependencies to install.** Three options:

### 1. Just open it
Double-click `index.html` — works offline (the only network call at load is the three.js CDN script).

### 2. Local server (recommended for live NASA data)
```bash
# from the repo root, any static server works:
python3 -m http.server 8000
#   then visit http://localhost:8000
```

### 3. GitHub Pages
Push to `main` and enable Pages (root). The app is a single `index.html` + `js/` folder — nothing else needed.

> **No API key required.** The app ships with the public `DEMO_KEY`, which works for ~30 requests/hour per endpoint (50 for APOD). Responses are cached for 6 hours, so normal browsing stays well within limits. For heavier use, paste your own free key from [api.nasa.gov](https://api.nasa.gov) into **Settings → NASA API Key**.

---

## 🧭 How to use it

### The Explore view
- **Drag** anywhere on the scene to orbit the camera.
- **Scroll / pinch** to zoom.
- **Right-drag** to pan.
- **Click a planet** (or use the left rail buttons) to fly the camera to it and open an info card.
- **◐ button** (top-right, or `O`): toggle cinematic auto-orbit.
- **♪ button** (`S`): toggle procedural ambient sound + SFX.

### The data panels (nav 02–07)
1. **Picture of the Day** — APOD, with a date picker.
2. **Mars Rovers** — Curiosity / Perseverance photos by sol + camera.
3. **Asteroids** — This week's near-Earth object close approaches, sorted by distance, with hazard flags.
4. **Earth Live** — DSCOVR/EPIC full-disc Earth imagery by date.
5. **Space Weather** — DONKI events (CME, flares, geomagnetic storms, …).
6. **Spinoffs** — NASA technology-transfer patents, software, and spinoffs.

### Capture & export
- **Quality** (right toolbar): High / Medium / Low — changes render fidelity.
- **Export Image**: pick PNG/JPEG + resolution (up to **8K = 7680×4320**) → downloads instantly. (`P` for a quick PNG.)
- **Record Video**: starts/stops a WebM capture of the live scene at 30 fps.

---

## 🗂 Project structure

```
.
├── index.html              ← the app (loads three.js from CDN, then the js/ modules)
├── js/
│   ├── i18n.js             ← 10-language switcher + translation table
│   ├── nasa.js             ← NASA API client: caching, fallbacks, all endpoints
│   ├── audio.js            ← procedural WebAudio ambient pad + SFX
│   ├── scene.js            ← the three.js solar system (shaders, planets, controls)
│   ├── export.js           ← PNG/JPEG up to 8K + WebM/MP4 video recording
│   ├── panels.js           ← the 6 live NASA data panels
│   └── app.js              ← controller: nav, settings, toolbar, boot
├── docs/
│   ├── ARCHITECTURE.md     ← how the modules fit together
│   ├── APIS.md             ← every NASA endpoint used, with params & examples
│   ├── RAY_TRACING.md      ← the lighting/shader model, with references
│   └── ACCESSIBILITY.md   ← keyboard, RTL, contrast, reduced-motion
├── worldcup-2026.html      ← the repo's original sibling project (preserved)
└── README.md               ← this file
```

---

## 🔌 The NASA APIs

All endpoints are documented in [`docs/APIS.md`](docs/APIS.md). Summary:

| Panel | Endpoint | What it returns |
|---|---|---|
| Picture of the Day | `/planetary/apod` | Daily astronomy image/video + explanation |
| Mars Rovers | `/mars-photos/api/v1/rovers[/photos]` | Rover manifest + photos by sol/camera |
| Asteroids | `/neo/rest/v1/feed` | Near-Earth object close approaches + hazard flags |
| Earth Live | `/EPIC/api/natural/date/{date}` | DSCOVR full-disc Earth frames + coordinates |
| Space Weather | `/DONKI/{type}` | CME, flares, geomagnetic storms, etc. |
| Spinoffs | `/techtransfer/{category}` | NASA patents / software / spinoffs |

---

## 🌍 Languages / Idiomas / 언어 / 语言

The interface is fully translated in **10 languages** and switchable live from **Settings → Language**. Translation strings live in `js/i18n.js` as a flat keyed table; adding an 11th language is a matter of adding its code to `langs` and providing values for each key.

- English · 中文 (Chinese) · Português (Portuguese) · Español (Spanish) · 한국어 (Korean) · Français (French) · Deutsch (German) · 日本語 (Japanese) · العربية (Arabic, RTL) · Русский (Russian)

---

## ⌨️ Keyboard shortcuts

| Key | Action |
|---|---|
| `1`–`7` | Switch panels (Explore, APOD, Mars, NEO, EPIC, Weather, Tech) |
| `S` | Toggle sound |
| `O` | Toggle auto-orbit |
| `P` | Quick PNG screenshot |

---

## 🛠 Technology

- **[three.js](https://threejs.org) r158** — the only external dependency, loaded from CDN.
- **WebGL** via three.js for real-time rendering; custom GLSL shaders for the Sun corona and Saturn's rings.
- **Web Audio API** — all sound is procedurally synthesized; no audio assets.
- **MediaRecorder API** (`canvas.captureStream`) — for video export.
- **`localStorage`** — for the API key, language, quality preference, and a 6-hour response cache.
- **Plain ES5-flavoured JS** — no bundler, no transpiler, no framework. Every module is a defensive IIFE that attaches to `window`.

---

## 🧪 Testing & verification

- All 7 JS modules pass `node --check` (syntax).
- A Node smoke test loads every module against a mocked browser environment and asserts: all public APIs exposed, i18n translates `app.title` in all 10 languages, and the NASA client's offline fallbacks return valid sample payloads.
- HTML element IDs referenced by `app.js` were cross-checked against `index.html` — all 20 present.
- The app degrades gracefully: if the network is blocked or the demo key is rate-limited, every panel shows a clearly-labelled **SAMPLE** badge with bundled representative data.

---

## 📄 License & attribution

- **NASA data** — © NASA, public domain / open data. Source: [api.nasa.gov](https://api.nasa.gov).
- **three.js** — MIT licensed. Source: [threejs.org](https://threejs.org).
- **Code** — see repository license; built for exploration and education.

---

## 🙏 Acknowledgements

Inspired by the open ray-tracing and graphics education community whose work the reference links in this project's commission point to — notably *Ray Tracing in One Weekend* (Peter Shirley), [RayTracing.github.io](https://raytracing.github.io/), [Scratchapixel](https://scratchapixel.com/), and the broader NASA open-data community that makes endpoints like these freely available.

---

*This repository also contains the original sibling project, **"300 Analysts, One Question"** — a data-driven 2026 FIFA World Cup forecast. It is preserved at [`worldcup-2026.html`](worldcup-2026.html) and [`docs/WORLDCUP_README.md`](docs/WORLDCUP_README.md), and is independent of COSMOS.*
