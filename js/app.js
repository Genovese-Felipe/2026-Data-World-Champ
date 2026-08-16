/*
 * COSMOS — main application controller
 * ---------------------------------------------------------------------------
 * Wires together every module:
 *   • COSMOS_SCENE  — the 3D solar system (three.js)
 *   • COSMOS_PANELS — the NASA data panels
 *   • COSMOS_EXPORT — image/video capture
 *   • COSMOS_AUDIO  — procedural sound
 *   • NASA          — the API client
 *   • I18n          — 10-language switcher
 *
 * Owns the nav, the settings drawer, the export toolbar, the language menu,
 * and the loading ritual. No framework — plain DOM, ~no deps.
 */
(function (global) {
  "use strict";

  var APP = {};
  var activePanel = "explore";
  var panelRoots = {};

  function $(sel, root) { return (root || document).querySelector(sel); }
  function $all(sel, root) { return Array.prototype.slice.call((root || document).querySelectorAll(sel)); }

  // ---- nav ----------------------------------------------------------------
  function initNav() {
    $all("[data-panel]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        showPanel(btn.dataset.panel);
        if (global.COSMOS_AUDIO) global.COSMOS_AUDIO.sfx("select");
      });
    });
  }

  function showPanel(name) {
    activePanel = name;
    $all("[data-panel]").forEach(function (b) {
      b.classList.toggle("active", b.dataset.panel === name);
    });
    $all(".panel-root").forEach(function (r) { r.classList.remove("active"); });

    var root = panelRoots[name];
    if (!root) {
      root = document.createElement("div");
      root.className = "panel-root";
      $("#panels").appendChild(root);
      panelRoots[name] = root;
    }
    root.classList.add("active");

    if (name === "explore") {
      $("#scene-container").classList.add("active");
      $("#scene-toolbar").classList.add("active");
      $("#scene-hint").classList.add("active");
    } else {
      $("#scene-container").classList.remove("active");
      $("#scene-toolbar").classList.remove("active");
      $("#scene-hint").classList.remove("active");
      renderPanel(name, root);
    }
  }

  function renderPanel(name, root) {
    if (name === "apod") COSMOS_PANELS.renderAPOD(root);
    else if (name === "mars") COSMOS_PANELS.renderMars(root);
    else if (name === "neo") COSMOS_PANELS.renderNEO(root);
    else if (name === "epic") COSMOS_PANELS.renderEPIC(root);
    else if (name === "weather") COSMOS_PANELS.renderWeather(root);
    else if (name === "tech") COSMOS_PANELS.renderTech(root);
  }

  APP.reloadActivePanel = function () {
    if (activePanel !== "explore" && panelRoots[activePanel]) {
      renderPanel(activePanel, panelRoots[activePanel]);
    }
  };

  // ---- settings drawer ---------------------------------------------------
  function initSettings() {
    var drawer = $("#settings-drawer");
    var backdrop = $("#settings-backdrop");

    $("#settings-btn").addEventListener("click", function () {
      drawer.classList.add("open"); backdrop.classList.add("open");
    });
    backdrop.addEventListener("click", function () {
      drawer.classList.remove("open"); backdrop.classList.remove("open");
    });

    // api key
    var keyInput = $("#apikey-input");
    keyInput.value = NASA.getKey() === NASA.DEMO_KEY ? "" : NASA.getKey();
    keyInput.addEventListener("change", function () {
      NASA.setKey(keyInput.value.trim());
      NASA.clearCache();
      APP.reloadActivePanel();
    });

    // language menu
    var langMenu = $("#lang-menu");
    Object.keys(I18n.langs).forEach(function (code) {
      var b = document.createElement("button");
      b.className = "lang-btn"; b.dataset.lang = code;
      b.innerHTML = '<span class="lang-code">' + code.toUpperCase() + '</span><span class="lang-name">' + I18n.langs[code] + '</span>';
      b.addEventListener("click", function () {
        I18n.set(code);
        $all(".lang-btn").forEach(function (x) { x.classList.toggle("active", x.dataset.lang === code); });
      });
      langMenu.appendChild(b);
    });
    // mark active
    var cur = I18n.get();
    $all(".lang-btn").forEach(function (x) { x.classList.toggle("active", x.dataset.lang === cur); });

    // clear cache button
    $("#clear-cache-btn").addEventListener("click", function () {
      NASA.clearCache();
      APP.reloadActivePanel();
      if (global.COSMOS_AUDIO) global.COSMOS_AUDIO.sfx("select");
    });
  }

  // ---- quality + sound toggles ------------------------------------------
  function initToggles() {
    // quality
    var qWrap = $("#quality-toggle");
    ["high", "medium", "low"].forEach(function (q) {
      var b = document.createElement("button");
      b.className = "qbtn"; b.dataset.q = q;
      b.setAttribute("data-i18n", "quality." + q);
      b.textContent = I18n.t("quality." + q);
      b.addEventListener("click", function () {
        $all(".qbtn", qWrap).forEach(function (x) { x.classList.remove("active"); });
        b.classList.add("active");
        COSMOS_SCENE.setQuality(q);
      });
      qWrap.appendChild(b);
    });
    // mark active
    var cq = COSMOS_SCENE.getQuality ? COSMOS_SCENE.getQuality() : "high";
    $all(".qbtn").forEach(function (x) { x.classList.toggle("active", x.dataset.q === cq); });

    // sound
    var sBtn = $("#sound-toggle");
    function syncSound() {
      var on = COSMOS_AUDIO.enabled;
      sBtn.classList.toggle("on", on);
      sBtn.setAttribute("data-i18n", "sound." + (on ? "on" : "off"));
      sBtn.textContent = I18n.t("sound." + (on ? "on" : "off"));
    }
    syncSound();
    sBtn.addEventListener("click", function () {
      COSMOS_AUDIO.toggle();
      // if just turned on and audio not yet started, unlock
      if (COSMOS_AUDIO.enabled) COSMOS_AUDIO.unlock();
      syncSound();
    });
    global.addEventListener("langchange", function () { syncSound(); });

    // orbit auto
    var oBtn = $("#orbit-toggle");
    oBtn.addEventListener("click", function () {
      var on = oBtn.classList.toggle("on");
      COSMOS_SCENE.setOrbitAuto(on);
    });
  }

  // ---- export toolbar ----------------------------------------------------
  function initExport() {
    var formatSel = $("#export-format");
    var resSel = $("#export-res");
    var imgBtn = $("#export-image-btn");
    var recBtn = $("#export-record-btn");

    imgBtn.addEventListener("click", function () {
      var fmt = formatSel.value;
      var res = resSel.value;
      var dims = {
        "1080p": [1920, 1080], "1440p": [2560, 1440],
        "4k": [3840, 2160], "8k": [7680, 4320]
      };
      var d = dims[res] || dims["1080p"];
      imgBtn.disabled = true; imgBtn.textContent = "…";
      COSMOS_EXPORT.image(fmt, d[0], d[1]).then(function () {
        imgBtn.disabled = false; imgBtn.textContent = I18n.t("action.export.image");
      }).catch(function () {
        imgBtn.disabled = false; imgBtn.textContent = I18n.t("action.export.image");
        if (global.COSMOS_AUDIO) global.COSMOS_AUDIO.sfx("error");
      });
    });

    recBtn.addEventListener("click", function () {
      if (COSMOS_EXPORT.isRecording) {
        COSMOS_EXPORT.stopVideo();
        recBtn.classList.remove("rec");
        recBtn.textContent = I18n.t("action.record");
      } else {
        var ok = COSMOS_EXPORT.startVideo(30);
        if (ok) {
          recBtn.classList.add("rec");
          recBtn.textContent = I18n.t("action.stop");
        } else if (global.COSMOS_AUDIO) COSMOS_AUDIO.sfx("error");
      }
    });
  }

  // ---- scene body selection -> fly + show info card ---------------------
  function initScene() {
    COSMOS_SCENE.init($("#scene-container"));
    COSMOS_SCENE.onSelect(function (name, data) {
      var card = $("#body-card");
      var localizedName = I18n.t("body." + name);
      card.querySelector(".bc-name").textContent = localizedName;
      card.querySelector(".bc-detail").textContent = describeBody(data);
      card.classList.add("show");
    });
    $("#body-card .bc-close").addEventListener("click", function () {
      $("#body-card").classList.remove("show");
    });
    // quick-jump planet buttons
    $all(".planet-jump").forEach(function (b) {
      b.addEventListener("click", function () {
        COSMOS_SCENE.focusBody(b.dataset.body);
        if (global.COSMOS_AUDIO) COSMOS_AUDIO.sfx("warp");
      });
    });
  }

  function describeBody(d) {
    var facts = {
      sun: "A G-type main-sequence star. 99.86% of the Solar System's mass. Surface ~5,500°C.",
      mercury: "Closest planet to the Sun. No atmosphere. Day/night swing from 430°C to −180°C.",
      venus: "Hottest planet (462°C) under a crushing CO₂ atmosphere. Rotates backwards.",
      earth: "The only known world with life. 71% surface water. One natural satellite, the Moon.",
      mars: "The Red Planet. Olympus Mons is the tallest volcano in the Solar System (21 km).",
      jupiter: "Largest planet. The Great Red Spot is a storm wider than Earth, raging for centuries.",
      saturn: "Famed for its spectacular ring system of ice and rock. Least dense planet — it would float.",
      uranus: "An ice giant tilted 98° — it rolls along its orbit on its side.",
      neptune: "The windiest planet: supersonic gales over 2,000 km/h. Discovered by mathematics first."
    };
    return facts[d.name] || "";
  }

  // ---- loading ritual ----------------------------------------------------
  function loadingRitual(done) {
    var bar = $("#load-bar-fill");
    var pct = 0;
    var iv = setInterval(function () {
      pct = Math.min(100, pct + Math.random() * 18 + 6);
      bar.style.width = pct + "%";
      $("#load-pct").textContent = Math.floor(pct) + "%";
      if (pct >= 100) {
        clearInterval(iv);
        setTimeout(function () {
          $("#loader").classList.add("hidden");
          if (global.COSMOS_AUDIO) COSMOS_AUDIO.sfx("warp");
          done();
        }, 350);
      }
    }, 120);
  }

  // ---- keyboard nav ------------------------------------------------------
  function initKeyboard() {
    global.addEventListener("keydown", function (e) {
      if (e.target.tagName === "INPUT" || e.target.tagName === "SELECT") return;
      var map = { "1": "explore", "2": "apod", "3": "mars", "4": "neo", "5": "epic", "6": "weather", "7": "tech" };
      if (map[e.key]) { showPanel(map[e.key]); if (global.COSMOS_AUDIO) COSMOS_AUDIO.sfx("select"); }
      if (e.key === "s") $("#sound-toggle").click();
      if (e.key === "o") $("#orbit-toggle").click();
      if (e.key === "p" || e.key === "P") $("#export-image-btn").click();
    });
  }

  // ---- first-gesture audio unlock ---------------------------------------
  function initAudioUnlock() {
    function unlock() {
      if (global.COSMOS_AUDIO) COSMOS_AUDIO.unlock();
      global.removeEventListener("pointerdown", unlock);
      global.removeEventListener("keydown", unlock);
    }
    global.addEventListener("pointerdown", unlock);
    global.addEventListener("keydown", unlock);
  }

  // ---- boot --------------------------------------------------------------
  APP.init = function () {
    I18n.apply(document);
    initNav();
    initSettings();
    initToggles();
    initExport();
    initKeyboard();
    initAudioUnlock();

    loadingRitual(function () {
      initScene();
      showPanel("explore");
    });

    // re-apply translations on language change
    global.addEventListener("langchange", function () {
      I18n.apply(document);
      // re-render the active panel so dynamic labels update
      APP.reloadActivePanel();
    });
  };

  global.COSMOS_APP = APP;
  // boot when DOM is ready + three.js loaded
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
      waitForThree(function () { APP.init(); });
    });
  } else {
    waitForThree(function () { APP.init(); });
  }

  function waitForThree(cb) {
    if (global.COSMOS_SCENE) cb();
    else setTimeout(function () { waitForThree(cb); }, 30);
  }
})(window);
