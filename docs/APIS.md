# NASA APIs used by COSMOS

All endpoints are from the **NASA Open APIs** portal at [api.nasa.gov](https://api.nasa.gov). Authentication is a single `api_key` query parameter. The app ships with the public `DEMO_KEY` (no signup) and lets users paste their own key in **Settings → NASA API Key**.

> **DEMO_KEY limits** (per [api.nasa.gov](https://api.nasa.gov/#overview)): 30 requests/hour per IP for most endpoints, 50/hour for APOD. COSMOS caches every response for 6 hours, so normal interactive use stays well within these limits.

The client (`js/nasa.js`) follows this contract for every call: **cache hit → fetch → write cache → on failure: return expired cache if any, else a bundled sample payload flagged `_sample: true`**. Each result object carries `{ data, cached, sample, stale?, error? }` so the UI can show a `LIVE / cached / SAMPLE` badge.

---

## 1. Astronomy Picture of the Day (APOD)

One of NASA's most popular services — a different image or video each day, with a written explanation by a professional astronomer.

- **Endpoint:** `GET https://api.nasa.gov/planetary/apod`
- **Key params:** `date` (YYYY-MM-DD), `start_date` / `end_date` (range), `thumbs` (return video thumbnail), `api_key`
- **Returns:** `media_type` (`image` or `video`), `url`, `hdurl`, `title`, `explanation`, `copyright`, `date`
- **Used by:** the "Picture of the Day" panel (`panels.renderAPOD`). The app shows the image, title, explanation, and credit, and offers a date picker. Video APODs are embedded via the YouTube URL.
- **Docs:** [api.nasa.gov/#apod](https://api.nasa.gov/#apod)

```js
NASA.apod("2024-03-14")   // → { data: { title, url, explanation, ... }, cached, sample }
```

---

## 2. Mars Rover Photos

Photos gathered by the Curiosity, Opportunity, Spirit, and Perseverance rovers, queryable by Martian sol (solar day since landing) and camera.

- **Manifest endpoint:** `GET https://api.nasa.gov/mars-photos/api/v1/rovers` — lists rovers, their status, max_sol, and available cameras.
- **Photos endpoint:** `GET https://api.nasa.gov/mars-photos/api/v1/rovers/{rover}/photos?sol={n}&camera={cam}&api_key=`
- **Returns:** `photos[]` each with `img_src`, `camera.name`, `earth_date`, `rover.name`
- **Used by:** the "Mars Rovers" panel (`panels.renderMars`). The rover dropdown is populated from the manifest; choosing a rover + sol fetches up to 24 thumbnails (click to open full-res).
- **Docs:** [api.nasa.gov/#mars-rover-photos](https://api.nasa.gov/#mars-rover-photos)

```js
NASA.marsRovers()                        // → manifest
NASA.marsPhotos("perseverance", 1100)    // → { data: { photos: [...] } }
```

---

## 3. Near Earth Object Web Service (NeoWs) — Asteroids

A RESTful service for near-Earth asteroid information: closest-approach dates, sizes, velocities, miss distances, and the **potentially hazardous** flag.

- **Feed endpoint:** `GET https://api.nasa.gov/neo/rest/v1/feed?start_date=&end_date=&api_key=`
- **Limit:** date range ≤ 7 days.
- **Returns:** `element_count` + `near_earth_objects` keyed by date, each object with `name`, `is_potentially_hazardous_asteroid`, `estimated_diameter` (km), and `close_approach_data[]` (miss_distance, relative_velocity, close_approach_date).
- **Used by:** the "Asteroids" panel (`panels.renderNEO`). The app flattens the week's NEOs into a sortable table, flags hazardous ones in red, and shows diameter / velocity / miss-distance.
- **Docs:** [api.nasa.gov/#neows-fireball](https://api.nasa.gov/#asteroids-neows)

```js
NASA.neoFeed("2024-03-01", "2024-03-07")
// → { data: { element_count, near_earth_objects: { "2024-03-01": [...] } } }
```

---

## 4. Earth Polychromatic Imaging Camera (EPIC)

Full-disc Earth imagery from the DSCOVR satellite at Lagrange point 1 — natural-color views of the sunlit Earth, several times a day.

- **Metadata endpoint:** `GET https://api.nasa.gov/EPIC/api/natural/date/{date}?api_key=`
- **Returns:** array of frames, each with `image` (filename), `date`, `caption`, and `centroid_coordinates` (lat/lon of the image center).
- **Image URL** (built by `NASA.epicImage(item)`): `https://api.nasa.gov/EPIC/archive/natural/{YYYY}/{MM}/{DD}/png/{image}.png?api_key=`
- **Used by:** the "Earth Live" panel (`panels.renderEPIC`). A date picker fetches the day's frames; the app shows up to 12 thumbnails with their capture time and sub-spacecraft coordinates.
- **Docs:** [api.nasa.gov/#epic](https://api.nasa.gov/#epic)

```js
NASA.epic("2024-03-10")          // → metadata array
NASA.epicImage(frameItem)        // → full PNG url
```

---

## 5. Space Weather Database (DONKI)

The Space Weather Database Of Notifications, Knowledge, Information — a comprehensive log of solar events: coronal mass ejections (CME), solar flares (FLR), solar energetic particles (SEP), magnetopause crossings (MPC), geomagnetic storms (GST), and radiation belt enhancements (RBE).

- **Endpoint:** `GET https://api.nasa.gov/DONKI/{type}?startDate=&endDate=&api_key=`
- **Types supported by COSMOS:** `CME`, `FLR`, `SEP`, `MPC`, `GST`, `RBE` (selectable in the UI).
- **Returns:** array of event objects with `activityID` / `flrID` / `cmeID`, `startTime` / `beginTime`, `note`, and often a `link` to details.
- **Used by:** the "Space Weather" panel (`panels.renderWeather`). An event-type dropdown + last-30-days window; the app lists up to 20 events with their time and note.
- **Docs:** [api.nasa.gov/#donki](https://api.nasa.gov/#donki)

```js
NASA.donki("CME", "2024-02-01", "2024-03-01")
// → { data: [{ activityID, startTime, note, link }, ...] }
```

---

## 6. TechTransfer / Spinoffs

NASA's technology transfer program — patents, open-source software releases, and commercial spinoffs derived from NASA work.

- **Endpoint:** `GET https://api.nasa.gov/techtransfer/{category}/?api_key=`
- **Categories:** `patent`, `software`, `spinoff` (selectable in the UI).
- **Returns:** `{ count, results[] }` where each result is an array `[id, title, description, link]`.
- **Used by:** the "Spinoffs" panel (`panels.renderTech`). A category dropdown fetches entries; the app shows title + description + an external link for each.
- **Docs:** [api.nasa.gov/#techtransfer](https://api.nasa.gov/#techtransfer)

```js
NASA.techTransfer("patent")
// → { data: { count, results: [[id, title, desc, link], ...] } }
```

---

## Resilience & rate-limit handling

| Situation | Behaviour |
|---|---|
| Fresh fetch succeeds | Cached for 6h; badge = **LIVE** |
| Within TTL cache hit | Served from `localStorage`; badge = **cached** |
| Network fails, expired cache exists | Served stale; badge = **cached·stale** |
| Network fails, no cache at all | Bundled sample payload; badge = **SAMPLE** (clearly flagged) |
| User changes API key | Cache is cleared; next fetch uses the new key |

This means the app is never blank: on a cold start with no network, every panel shows representative sample data clearly labelled as such, and flips to live data the moment a fetch succeeds.
