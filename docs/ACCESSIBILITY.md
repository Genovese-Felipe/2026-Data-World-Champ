# Accessibility

COSMOS is built to be usable with keyboard, mouse, touch, and assistive tech, across languages including right-to-left Arabic, and on devices from phones to 8K workstations.

## Keyboard

| Key | Action |
|---|---|
| `1`–`7` | Switch panels (Explore → APOD → Mars → Asteroids → Earth → Weather → Spinoffs) |
| `S` | Toggle sound |
| `O` | Toggle cinematic auto-orbit |
| `P` | Quick PNG screenshot |

The keyboard handler deliberately ignores keypresses while focus is in an `<input>` or `<select>` so typing a date or API key doesn't trigger panel switches.

## Mouse / touch

- **OrbitControls** provide drag-orbit, scroll-zoom, and right-drag pan on desktop.
- On touch devices, one-finger drag orbits and pinch zooms — the same control surface, no separate code path.
- All interactive elements are real `<button>` / `<select>` / `<a>` elements, focusable and operable by keyboard.

## Internationalization & RTL

- 10 languages: English, 中文, Português, Español, 한국어, Français, Deutsch, 日本語, العربية, Русский.
- Arabic triggers `dir="rtl"` on `<html>`; the layout uses logical properties and flexbox so it mirrors correctly.
- Language choice persists in `localStorage` and is applied on every load before first paint.
- Adding a language: add its code to `I18n.langs` (and to the `rtl` map if RTL), then provide a value for each key in `STRINGS`. The UI's language grid auto-populates from `I18n.langs`.

## Reduced motion

The cinematic **auto-orbit** mode is opt-in (the ◐ button or `O`), never on by default. Users who prefer reduced motion can leave it off; the planets still orbit and spin, but the camera stays where they placed it. A future enhancement could honor `prefers-reduced-motion` to also slow the planet rotation rates.

## Contrast & colour

- The dark `--void` ground (`#05060f`) with `--ink` text (`#e8eaf2`) exceeds WCAG AA contrast for body text.
- Interactive accents use NASA's own red (`#fc3d21`) and a high-luminance cyan (`#00d4ff`) for strong visibility against the dark ground.
- Status badges (LIVE / cached / SAMPLE / hazard) use both colour *and* text labels, so colour-blind users are never dependent on hue alone.

## Status transparency

Every NASA data panel surfaces a status badge so users always know whether they're seeing fresh live data, cached data, or a bundled sample:
- **LIVE** (green) — fresh fetch from NASA.
- **cached** (cyan) — served from the 6-hour `localStorage` cache.
- **cached·stale** — network failed but an expired cache was available.
- **SAMPLE** (amber) — bundled fallback; clearly flagged so it's never mistaken for live data.

## Responsiveness

- The layout is mobile-first with a 768px breakpoint: the planet quick-jump rail and the right-side toolbar collapse/reposition on small screens.
- The 3D canvas fills the viewport and resizes on `window.resize`.
- Quality presets let users on low-power devices drop to Low (lower DPR, fewer stars, no shadows) for a smooth framerate.

## Offline resilience

If the network is blocked or the demo key is rate-limited, every panel renders a bundled sample payload rather than an error or empty state. The app remains explorable and presentable even fully offline (the only hard network dependency is the three.js CDN script on first load; subsequent loads are served from the browser cache).
