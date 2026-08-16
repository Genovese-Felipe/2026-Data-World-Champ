/*
 * COSMOS — NASA data panels
 * ---------------------------------------------------------------------------
 * Builds the live, i18n-aware UI for each NASA endpoint:
 *   • APOD  — Astronomy Picture of the Day (with date picker + gallery)
 *   • Mars  — Rover photos (rover + sol selectors)
 *   • NEO   — Asteroid close-approach feed (sortable, hazard flags)
 *   • EPIC  — DSCOVR Earth imagery gallery
 *   • DONKI — Space-weather event log
 *   • Tech  — NASA spinoff patents/software
 *
 * Each panel shows a status badge: LIVE (fresh fetch), cached, or SAMPLE
 * (bundled fallback — clearly flagged). All strings go through I18n.t().
 *
 * Public surface (window.COSMOS_PANELS):
 *   COSMOS_PANELS.renderAPOD(el)
 *   COSMOS_PANELS.renderMars(el)
 *   COSMOS_PANELS.renderNEO(el)
 *   COSMOS_PANELS.renderEPIC(el)
 *   COSMOS_PANELS.renderWeather(el)
 *   COSMOS_PANELS.renderTech(el)
 *   COSMOS_PANELS.refreshAll()
 */
(function (global) {
  "use strict";

  function el(tag, cls, html) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (html != null) n.innerHTML = html;
    return n;
  }

  function statusBadge(res) {
    if (res.sample) return '<span class="badge badge-sample" data-i18n="status.sample">' + I18n.t("status.sample") + "</span>";
    if (res.cached && res.stale) return '<span class="badge badge-stale">cached·stale</span>';
    if (res.cached) return '<span class="badge badge-cached" data-i18n="status.cached">' + I18n.t("status.cached") + "</span>";
    return '<span class="badge badge-live" data-i18n="status.live">' + I18n.t("status.live") + "</span>";
  }

  function fmtNum(n, d) { d = d == null ? 0 : d; return Number(n).toLocaleString(undefined, { maximumFractionDigits: d }); }

  // =====================================================================
  // APOD
  // =====================================================================
  function renderAPOD(container) {
    container.innerHTML = "";
    container.appendChild(el("div", "panel-head", "<h2 data-i18n='nav.apod'>" + I18n.t("nav.apod") + "</h2>"));
    var picker = el("div", "date-picker", "");
    var input = el("input"); input.type = "date";
    input.max = I18n ? NASA.todayISO() : "";
    input.value = NASA.todayISO();
    var goBtn = el("button", "btn", "→");
    picker.appendChild(input); picker.appendChild(goBtn);
    container.appendChild(picker);

    var stage = el("div", "apod-stage", "");
    container.appendChild(stage);

    function load(date) {
      stage.innerHTML = '<div class="spinner"></div>';
      NASA.apod(date).then(function (res) {
        var d = res.data;
        stage.innerHTML = "";
        var meta = el("div", "panel-meta", statusBadge(res) + "<span class='apod-date'>" + (d.date || date) + "</span>");
        stage.appendChild(meta);
        var title = el("h3", "apod-title", (d.title || "").replace(/</g, "&lt;"));
        stage.appendChild(title);
        if (d.media_type === "video" && d.url) {
          stage.appendChild(el("div", "apod-media", '<iframe src="' + d.url + '" frameborder="0" allowfullscreen></iframe>'));
        } else {
          var imgWrap = el("a", "apod-media");
          imgWrap.href = d.hdurl || d.url; imgWrap.target = "_blank";
          imgWrap.innerHTML = '<img src="' + (d.url || "") + '" alt="' + (d.title || "") + '" loading="lazy">';
          stage.appendChild(imgWrap);
        }
        stage.appendChild(el("p", "apod-explain", (d.explanation || "").replace(/</g, "&lt;")));
        if (d.copyright) stage.appendChild(el("p", "apod-credit", "© " + d.copyright));
        I18n.apply(stage);
      });
    }
    goBtn.onclick = function () { load(input.value); if (global.COSMOS_AUDIO) global.COSMOS_AUDIO.sfx("select"); };
    input.onkeydown = function (e) { if (e.key === "Enter") load(input.value); };
    load(input.value);
  }

  // =====================================================================
  // Mars Rover photos
  // =====================================================================
  function renderMars(container) {
    container.innerHTML = "";
    container.appendChild(el("div", "panel-head", "<h2 data-i18n='nav.mars'>" + I18n.t("nav.mars") + "</h2>"));

    // populate rover selector from manifest (with fallback)
    var controls = el("div", "mars-controls", "");
    var roverSel = el("select", ""), solIn = el("input");
    solIn.type = "number"; solIn.value = 1000; solIn.min = 0;
    var goBtn = el("button", "btn", "→");
    controls.appendChild(roverSel); controls.appendChild(el("span", "field-label", "Sol:")); controls.appendChild(solIn); controls.appendChild(goBtn);
    container.appendChild(controls);

    var gallery = el("div", "mars-gallery", "");
    container.appendChild(gallery);

    NASA.marsRovers().then(function (res) {
      var rovers = (res.data && res.data.rovers) || [];
      roverSel.innerHTML = "";
      rovers.forEach(function (rv) {
        var opt = el("option", "", rv.name);
        opt.value = rv.name.toLowerCase();
        opt.dataset.maxsol = rv.max_sol;
        roverSel.appendChild(opt);
      });
      // if a rover chosen, default sol to its max
      if (roverSel.options.length) {
        var first = roverSel.options[0];
        solIn.max = first.dataset.maxsol;
      }
    });

    function load() {
      var rover = roverSel.value || "curiosity";
      var sol = parseInt(solIn.value, 10) || 0;
      gallery.innerHTML = '<div class="spinner"></div>';
      NASA.marsPhotos(rover, sol).then(function (res) {
        var photos = (res.data && res.data.photos) || [];
        gallery.innerHTML = "";
        gallery.appendChild(el("div", "panel-meta", statusBadge(res) +
          "<span>" + fmtNum(photos.length) + " photos · rover " + rover + " · sol " + sol + "</span>"));
        if (!photos.length) { gallery.appendChild(el("p", "empty", "No photos for this sol. Try a different sol or rover.")); return; }
        photos.slice(0, 24).forEach(function (p) {
          var card = el("figure", "photo-card");
          var img = el("img"); img.src = p.img_src; img.loading = "lazy"; img.alt = "Mars photo " + p.id;
          card.appendChild(img);
          card.appendChild(el("figcaption", "", (p.camera ? p.camera.name : "") + " · " + (p.earth_date || "")));
          card.onclick = function () { window.open(p.img_src, "_blank"); if (global.COSMOS_AUDIO) global.COSMOS_AUDIO.sfx("select"); };
          gallery.appendChild(card);
        });
        I18n.apply(gallery);
      });
    }
    goBtn.onclick = function () { load(); if (global.COSMOS_AUDIO) global.COSMOS_AUDIO.sfx("select"); };
    solIn.onkeydown = function (e) { if (e.key === "Enter") load(); };
    roverSel.onchange = function () {
      var opt = roverSel.options[roverSel.selectedIndex];
      if (opt && opt.dataset.maxsol) { solIn.max = opt.dataset.maxsol; }
    };
    load();
  }

  // =====================================================================
  // NEO asteroid feed
  // =====================================================================
  function renderNEO(container) {
    container.innerHTML = "";
    container.appendChild(el("div", "panel-head", "<h2 data-i18n='nav.neo'>" + I18n.t("nav.neo") + "</h2>"));

    var list = el("table", "neo-table", "");
    var wrap = el("div", "table-wrap", ""); wrap.appendChild(list);
    container.appendChild(wrap);

    NASA.neoFeed().then(function (res) {
      var neo = (res.data && res.data.near_earth_objects) || {};
      var rows = [];
      Object.keys(neo).forEach(function (date) {
        neo[date].forEach(function (a) {
          var ca = (a.close_approach_data && a.close_approach_data[0]) || {};
          var dist = ca.miss_distance ? fmtNum(parseFloat(ca.miss_distance.kilometers), 0) : "—";
          var vel = ca.relative_velocity ? fmtNum(parseFloat(ca.relative_velocity.kilometers_per_hour), 0) : "—";
          var dia = a.estimated_diameter ? fmtNum(a.estimated_diameter.kilometers.estimated_diameter_max * 1000, 0) : "—";
          rows.push({ hazard: a.is_potentially_hazardous_asteroid, name: a.name, date: (ca.close_approach_date || date), dist: dist, vel: vel, dia: dia });
        });
      });
      // sort by distance ascending
      rows.sort(function (a, b) { return parseFloat(a.dist.replace(/,/g, "")) - parseFloat(b.dist.replace(/,/g, "")); });

      list.innerHTML = "<thead><tr><th>Name</th><th>Date</th><th>Miss (km)</th><th>Vel (km/h)</th><th>Dia (m)</th><th>Risk</th></tr></thead>";
      var tb = el("tbody", "", "");
      rows.slice(0, 30).forEach(function (r) {
        var tr = el("tr", r.hazard ? "hazard" : "");
        tr.innerHTML = "<td>" + r.name + "</td><td>" + r.date + "</td><td>" + r.dist + "</td><td>" + r.vel + "</td><td>" + r.dia + "</td>" +
          "<td>" + (r.hazard ? '<span class="badge badge-hazard" data-i18n="panel.hazard">' + I18n.t("panel.hazard") + "</span>"
                              : '<span class="badge badge-safe" data-i18n="panel.nohazard">' + I18n.t("panel.nohazard") + "</span>") + "</td>";
        tb.appendChild(tr);
      });
      list.appendChild(tb);
      var meta = el("div", "panel-meta", statusBadge(res) + "<span>" + fmtNum((res.data && res.data.element_count) || rows.length) + " near-Earth objects this week</span>");
      container.insertBefore(meta, wrap);
      I18n.apply(list);
    });
  }

  // =====================================================================
  // EPIC Earth imagery
  // =====================================================================
  function renderEPIC(container) {
    container.innerHTML = "";
    container.appendChild(el("div", "panel-head", "<h2 data-i18n='nav.epic'>" + I18n.t("nav.epic") + "</h2>"));
    var picker = el("div", "date-picker", "");
    var input = el("input"); input.type = "date";
    input.value = NASA.todayISO(-1); input.max = NASA.todayISO();
    var goBtn = el("button", "btn", "→");
    picker.appendChild(input); picker.appendChild(goBtn);
    container.appendChild(picker);

    var gallery = el("div", "epic-gallery", "");
    container.appendChild(gallery);

    function load(date) {
      gallery.innerHTML = '<div class="spinner"></div>';
      NASA.epic(date).then(function (res) {
        var items = res.data || [];
        if (!Array.isArray(items)) items = [];
        gallery.innerHTML = "";
        gallery.appendChild(el("div", "panel-meta", statusBadge(res) + "<span>" + items.length + " frames</span>"));
        if (!items.length) { gallery.appendChild(el("p", "empty", "No EPIC frames for this date.")); return; }
        items.slice(0, 12).forEach(function (it) {
          var card = el("figure", "epic-card");
          var img = el("img"); img.loading = "lazy";
          if (it._sample) img.src = "https://epic.gsfc.nasa.gov/archive/natural/2017/01/01/png/epic_1b_20170101003000.png";
          else img.src = NASA.epicImage(it);
          img.alt = it.caption || "EPIC Earth";
          card.appendChild(img);
          card.appendChild(el("figcaption", "", (it.date || "").replace(" ", " · ") +
            (it.centroid_coordinates ? " · " + fmtNum(it.centroid_coordinates.lat, 1) + "°, " + fmtNum(it.centroid_coordinates.lon, 1) + "°" : "")));
          gallery.appendChild(card);
        });
        I18n.apply(gallery);
      });
    }
    goBtn.onclick = function () { load(input.value); if (global.COSMOS_AUDIO) global.COSMOS_AUDIO.sfx("select"); };
    input.onkeydown = function (e) { if (e.key === "Enter") load(input.value); };
    load(input.value);
  }

  // =====================================================================
  // DONKI space weather
  // =====================================================================
  function renderWeather(container) {
    container.innerHTML = "";
    container.appendChild(el("div", "panel-head", "<h2 data-i18n='nav.weather'>" + I18n.t("nav.weather") + "</h2>"));

    var typeSel = el("select", "");
    ["CME", "FLR", "SEP", "MPC", "GST", "RBE"].forEach(function (t) {
      var o = el("option", "", t); o.value = t; typeSel.appendChild(o);
    });
    var goBtn = el("button", "btn", "→");
    var controls = el("div", "mars-controls", "");
    controls.appendChild(el("span", "field-label", "Event:")); controls.appendChild(typeSel); controls.appendChild(goBtn);
    container.appendChild(controls);

    var log = el("div", "weather-log", "");
    container.appendChild(log);

    function load() {
      var type = typeSel.value;
      log.innerHTML = '<div class="spinner"></div>';
      NASA.donki(type).then(function (res) {
        var events = res.data || [];
        if (!Array.isArray(events)) events = [];
        log.innerHTML = "";
        log.appendChild(el("div", "panel-meta", statusBadge(res) + "<span>" + events.length + " events (last 30 days)</span>"));
        if (!events.length) { log.appendChild(el("p", "empty", "No events in this window.")); return; }
        events.slice(0, 20).forEach(function (ev) {
          var item = el("div", "weather-item");
          var title = ev.activityID || ev.flrID || ev.cmeID || ev.messageType || "Event";
          var time = ev.startTime || ev.beginTime || ev.eventTime || "";
          item.innerHTML = "<div class='wi-head'><b>" + title + "</b><span>" + (time || "") + "</span></div>" +
            (ev.note ? "<div class='wi-note'>" + ev.note.replace(/</g, "&lt;") + "</div>" : "") +
            (ev.link ? "<a href='" + ev.link + "' target='_blank' class='wi-link'>details ↗</a>" : "");
          log.appendChild(item);
        });
        I18n.apply(log);
      });
    }
    goBtn.onclick = function () { load(); if (global.COSMOS_AUDIO) global.COSMOS_AUDIO.sfx("select"); };
    typeSel.onchange = load;
    load();
  }

  // =====================================================================
  // TechTransfer spinoffs
  // =====================================================================
  function renderTech(container) {
    container.innerHTML = "";
    container.appendChild(el("div", "panel-head", "<h2 data-i18n='nav.tech'>" + I18n.t("nav.tech") + "</h2>"));

    var catSel = el("select", "");
    [["patent", "Patents"], ["software", "Software"], ["spinoff", "Spinoffs"]].forEach(function (c) {
      var o = el("option", "", c[1]); o.value = c[0]; catSel.appendChild(o);
    });
    var goBtn = el("button", "btn", "→");
    var controls = el("div", "mars-controls", "");
    controls.appendChild(el("span", "field-label", "Category:")); controls.appendChild(catSel); controls.appendChild(goBtn);
    container.appendChild(controls);

    var list = el("div", "tech-list", "");
    container.appendChild(list);

    function load() {
      var cat = catSel.value;
      list.innerHTML = '<div class="spinner"></div>';
      NASA.techTransfer(cat).then(function (res) {
        var results = (res.data && res.data.results) || [];
        list.innerHTML = "";
        list.appendChild(el("div", "panel-meta", statusBadge(res) + "<span>" + fmtNum((res.data && res.data.count) || results.length) + " entries</span>"));
        if (!results.length) { list.appendChild(el("p", "empty", "No entries.")); return; }
        results.slice(0, 20).forEach(function (r) {
          // results are arrays: [id, title, description, link]
          var item = el("div", "tech-item");
          item.innerHTML = "<h4>" + (r[1] || "Entry " + r[0]).replace(/</g, "&lt;") + "</h4>" +
            "<p>" + (r[2] || "").replace(/</g, "&lt;") + "</p>" +
            (r[3] ? "<a href='" + r[3] + "' target='_blank' class='wi-link'>open ↗</a>" : "");
          list.appendChild(item);
        });
        I18n.apply(list);
      });
    }
    goBtn.onclick = function () { load(); if (global.COSMOS_AUDIO) global.COSMOS_AUDIO.sfx("select"); };
    catSel.onchange = load;
    load();
  }

  function refreshAll() {
    NASA.clearCache();
    // panels re-fetch on next render; trigger the active panel
    if (global.COSMOS_APP && global.COSMOS_APP.reloadActivePanel) global.COSMOS_APP.reloadActivePanel();
  }

  global.COSMOS_PANELS = {
    renderAPOD: renderAPOD, renderMars: renderMars, renderNEO: renderNEO,
    renderEPIC: renderEPIC, renderWeather: renderWeather, renderTech: renderTech,
    refreshAll: refreshAll
  };
})(window);
