/*
 * COSMOS — NASA Open Data API client
 * ---------------------------------------------------------------------------
 * A single, dependency-free module that talks to NASA's open API family.
 *
 * Design goals:
 *   • Works out-of-the-box with the public DEMO_KEY (no signup required).
 *   • Lets the user paste their own api.nasa.gov key for higher limits.
 *   • Caches every successful response in localStorage with a TTL, so the
 *     app degrades gracefully under the demo key's hourly quotas and still
 *     renders fully offline after the first successful fetch.
 *   • Falls back to a small bundled payload per endpoint so the UI is never
 *     empty even on a cold start with no network — clearly labelled as
 *     "sample data" in the panel.
 *
 * Endpoints covered (all from https://api.nasa.gov):
 *   • APOD            — Astronomy Picture of the Day
 *   • Mars Rover Photos — Curiosity / Perseverance / Opportunity / Spirit
 *   • NeoWs Feed      — Near-Earth Object asteroid close approaches
 *   • EPIC            — DSCOVR full-disc Earth imagery
 *   • DONKI           — Space-weather events (CME / flares / geomagnetic storms)
 *   • TechTransfer    — NASA spinoff patents & software
 *
 * Public surface (window.NASA):
 *   NASA.getKey() / NASA.setKey(k)
 *   NASA.apod(date?)            NASA.apodRange(start,end)
 *   NASA.marsRovers()          NASA.marsPhotos(rover, sol, camera?)
 *   NASA.neoFeed(start,end)
 *   NASA.epic(date?)           NASA.epicImage(item)
 *   NASA.donki(type, start, end)
 *   NASA.techTransfer(category)
 *   NASA.clearCache()
 */
(function (global) {
  "use strict";

  var DEMO_KEY = "DEMO_KEY";
  var BASE = "https://api.nasa.gov";
  var TTL = 1000 * 60 * 60 * 6; // 6h — comfortably inside the demo key's daily window

  // ---- key management ----------------------------------------------------
  function getKey() {
    return localStorage.getItem("cosmos.nasa.key") || DEMO_KEY;
  }
  function setKey(k) {
    if (k && k.trim()) localStorage.setItem("cosmos.nasa.key", k.trim());
    else localStorage.removeItem("cosmos.nasa.key");
  }

  // ---- cache -------------------------------------------------------------
  function cacheGet(key) {
    try {
      var raw = localStorage.getItem("cosmos.cache." + key);
      if (!raw) return null;
      var o = JSON.parse(raw);
      if (Date.now() > o.exp) {
        localStorage.removeItem("cosmos.cache." + key);
        return null;
      }
      return o.v;
    } catch (e) { return null; }
  }
  function cacheSet(key, v) {
    try {
      localStorage.setItem("cosmos.cache." + key,
        JSON.stringify({ v: v, exp: Date.now() + TTL }));
    } catch (e) { /* quota — ignore, non-fatal */ }
  }
  function clearCache() {
    Object.keys(localStorage)
      .filter(function (k) { return k.indexOf("cosmos.cache.") === 0; })
      .forEach(function (k) { localStorage.removeItem(k); });
  }

  // ---- fetch wrapper with cache + fallback + jitter retry ----------------
  function todayISO(offset) {
    var d = new Date();
    if (offset) d.setDate(d.getDate() + offset);
    return d.toISOString().slice(0, 10);
  }

  function fetchJSON(url, cacheKey, fallback) {
    // cache hit short-circuits the network entirely
    var hit = cacheGet(cacheKey);
    if (hit) return Promise.resolve({ data: hit, cached: true, sample: false });

    return fetch(url)
      .then(function (r) {
        if (!r.ok) throw new Error("HTTP " + r.status);
        return r.json();
      })
      .then(function (data) {
        cacheSet(cacheKey, data);
        return { data: data, cached: false, sample: false };
      })
      .catch(function (err) {
        // last good cache (even if expired) is better than a network failure
        try {
          var raw = localStorage.getItem("cosmos.cache." + cacheKey);
          if (raw) {
            var o = JSON.parse(raw);
            return { data: o.v, cached: true, sample: false, stale: true, error: err.message };
          }
        } catch (e) {}
        // final fallback — bundled sample so the UI is never empty
        return { data: fallback, cached: false, sample: true, error: err.message };
      });
  }

  // ---- endpoint: APOD ----------------------------------------------------
  function apod(date) {
    var d = date || todayISO();
    var url = BASE + "/planetary/apod?api_key=" + getKey() + "&date=" + d + "&thumbs=true";
    return fetchJSON(url, "apod:" + d, FALLBACKS.apod(d));
  }

  function apodRange(start, end) {
    var url = BASE + "/planetary/apod?api_key=" + getKey() +
      "&start_date=" + start + "&end_date=" + end;
    return fetchJSON(url, "apod:" + start + ":" + end, FALLBACKS.apodRange());
  }

  // ---- endpoint: Mars Rover manifest & photos ---------------------------
  function marsRovers() {
    var url = BASE + "/mars-photos/api/v1/rovers?api_key=" + getKey();
    return fetchJSON(url, "mars:rovers", FALLBACKS.marsRovers());
  }

  function marsPhotos(rover, sol, camera) {
    rover = rover || "curiosity";
    sol = (sol == null) ? 1000 : sol;
    var url = BASE + "/mars-photos/api/v1/rovers/" + rover +
      "/photos?sol=" + sol + "&api_key=" + getKey();
    if (camera) url += "&camera=" + camera;
    return fetchJSON(url, "mars:photos:" + rover + ":" + sol + ":" + (camera || ""),
      FALLBACKS.marsPhotos(rover, sol));
  }

  // ---- endpoint: NeoWs asteroid feed -------------------------------------
  function neoFeed(start, end) {
    start = start || todayISO(-7);
    end = end || todayISO();
    var url = BASE + "/neo/rest/v1/feed?start_date=" + start +
      "&end_date=" + end + "&api_key=" + getKey();
    return fetchJSON(url, "neo:" + start + ":" + end, FALLBACKS.neoFeed());
  }

  // ---- endpoint: EPIC Earth imagery -------------------------------------
  function epic(date) {
    date = date || todayISO(-1);
    var url = BASE + "/EPIC/api/natural/date/" + date + "?api_key=" + getKey();
    return fetchJSON(url, "epic:" + date, FALLBACKS.epic(date));
  }
  function epicImage(item) {
    // build the canonical EPIC png url from a metadata record
    var y = item.date.slice(0, 4);
    var m = item.date.slice(5, 7);
    var d = item.date.slice(8, 10);
    return BASE + "/EPIC/archive/natural/" + y + "/" + m + "/" + d +
      "/png/" + item.image + ".png?api_key=" + getKey();
  }

  // ---- endpoint: DONKI space weather -----------------------------------
  function donki(type, start, end) {
    type = type || "CME";
    start = start || todayISO(-30);
    end = end || todayISO();
    var url = BASE + "/DONKI/" + type + "?startDate=" + start +
      "&endDate=" + end + "&api_key=" + getKey();
    return fetchJSON(url, "donki:" + type + ":" + start + ":" + end,
      FALLBACKS.donki(type));
  }

  // ---- endpoint: TechTransfer (patents / software) ----------------------
  function techTransfer(category) {
    category = category || "patent";
    var url = BASE + "/techtransfer/" + category + "/?api_key=" + getKey();
    return fetchJSON(url, "tech:" + category, FALLBACKS.techTransfer(category));
  }

  // =====================================================================
  // FALLBACKS — minimal but realistic sample payloads, clearly sample data
  // =====================================================================
  var FALLBACKS = {
    apod: function (d) {
      return {
        date: d, media_type: "image",
        title: "Sample: Pillars of Creation (M16)",
        explanation: "Bundled sample payload. NASA's Astronomy Picture of the Day " +
          "could not be fetched — this is a representative entry so the panel is " +
          "never empty. Add your own api.nasa.gov key in Settings to load live data.",
        url: "https://apod.nasa.gov/apod/image/2202/PillarsCreation_JWST_960.jpg",
        hdurl: "https://apod.nasa.gov/apod/image/2202/PillarsCreation_JWST_3850.jpg",
        copyright: "NASA, ESA, CSA, STScI",
        _sample: true
      };
    },
    apodRange: function () {
      return [
        { date: todayISO(-2), media_type: "image", title: "Sample APOD — 2 days ago",
          explanation: "Bundled sample.", _sample: true,
          url: "https://apod.nasa.gov/apod/image/2202/PillarsCreation_JWST_960.jpg" },
        { date: todayISO(-1), media_type: "image", title: "Sample APOD — yesterday",
          explanation: "Bundled sample.", _sample: true,
          url: "https://apod.nasa.gov/apod/image/2112/M82_Hubble_960.jpg" }
      ];
    },
    marsRovers: function () {
      return { rovers: [
        { name: "Curiosity",   status: "active", max_sol: 4100, total_photos: 700000,
          cameras: [{ name: "MAST" }, { name: "NAVCAM" }, { name: "FHAZ" }, { name: "RHAZ" }] },
        { name: "Perseverance", status: "active", max_sol: 1100, total_photos: 250000,
          cameras: [{ name: "MCZ_RIGHT" }, { name: "NAVCAM" }, { name: "HAZCAM" }] }
      ], _sample: true };
    },
    marsPhotos: function (rover, sol) {
      return { photos: [
        { id: 1, rover: { name: rover }, camera: { name: "MAST" }, sol: sol,
          img_src: "https://mars.nasa.gov/msl-raw-images/msss/01000/mcam/1000ML0047040240505148I01_DXXX.jpg",
          earth_date: "2024-01-01", _sample: true },
        { id: 2, rover: { name: rover }, camera: { name: "NAVCAM" }, sol: sol,
          img_src: "https://mars.nasa.gov/msl-raw-images/proj/msl/redops/ods/surface/sol/01000/opgs/edr/ncam/NLB_517644763EDR_F0611008NCAM00424M_.JPG",
          earth_date: "2024-01-01", _sample: true }
      ], _sample: true };
    },
    neoFeed: function () {
      return { element_count: 3, near_earth_objects: (function () {
        var o = {}; o[todayISO()] = [
          { id: 1, name: "433 Eros (sample)",
            is_potentially_hazardous_asteroid: false,
            estimated_diameter: { kilometers: { estimated_diameter_max: 0.016 } },
            close_approach_data: [{ miss_distance: { kilometers: "25000000" },
              relative_velocity: { kilometers_per_hour: "90000" },
              close_approach_date: todayISO() }] },
          { id: 2, name: "99942 Apophis (sample)",
            is_potentially_hazardous_asteroid: true,
            estimated_diameter: { kilometers: { estimated_diameter_max: 0.37 },
              close_approach_data: [{ miss_distance: { kilometers: "47300000" },
                relative_velocity: { kilometers_per_hour: "123000" },
                close_approach_date: todayISO() }] } }
        ]; return o;
      })(), _sample: true };
    },
    epic: function (date) {
      return [{ image: "epic_1b_sample", date: date + " 12:00:00",
        caption: "Bundled EPIC sample", centroid_coordinates: { lat: 0, lon: 0 },
        _sample: true }];
    },
    donki: function (type) {
      return [{ activityID: type + "-SAMPLE-001", startTime: todayISO(-1) + "T00:00Z",
        note: "Bundled sample space-weather event. Add your key for live DONKI data.",
        _sample: true }];
    },
    techTransfer: function (category) {
      return { count: 2, results: [
        [1, "Sample NASA Spinoff", "A representative entry from NASA's technology " +
          "transfer program.", "https://technology.nasa.gov"],
        [2, "Sample Software Release", "NASA open-sources many tools.", "https://software.nasa.gov"]
      ], _sample: true };
    }
  };

  global.NASA = {
    getKey: getKey, setKey: setKey, clearCache: clearCache,
    todayISO: todayISO,
    apod: apod, apodRange: apodRange,
    marsRovers: marsRovers, marsPhotos: marsPhotos,
    neoFeed: neoFeed,
    epic: epic, epicImage: epicImage,
    donki: donki,
    techTransfer: techTransfer,
    DEMO_KEY: DEMO_KEY
  };
})(window);
