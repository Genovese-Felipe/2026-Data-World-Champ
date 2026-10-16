/*
 * COSMOS — Audio engine (procedural WebAudio, no external assets)
 * ---------------------------------------------------------------------------
 * Everything is synthesized at runtime with the Web Audio API, so there are
 * zero audio files to ship and no licensing concerns. Two layers:
 *
 *   • Ambient pad — a slow, evolving drone of detuned oscillators + a soft
 *     low-pass filter sweep + a gentle LFO on the master gain. Gives the
 *     app an immersive "deep space" bed. Started on first user gesture
 *     (autoplay-policy safe).
 *   • SFX — short one-shot envelopes for UI feedback: hover, select,
 *     shutter (screenshot), record start/stop, error. Each is a tiny
 *     oscillator+gain graph triggered on demand.
 *
 * Public surface (window.COSMOS_AUDIO):
 *   COSMOS_AUDIO.enable() / .disable()
 *   COSMOS_AUDIO.toggle() -> bool
 *   COSMOS_AUDIO.enabled
 *   COSMOS_AUDIO.sfx(name)
 *   COSMOS_AUDIO.setAmbientVolume(0..1)
 */
(function (global) {
  "use strict";

  var ctx = null;
  var master = null;
  var ambient = null;
  var enabled = false;

  function ensureCtx() {
    if (ctx) return ctx;
    var AC = global.AudioContext || global.webkitAudioContext;
    if (!AC) return null;
    ctx = new AC();
    master = ctx.createGain();
    master.gain.value = 0.5;
    master.connect(ctx.destination);
    return ctx;
  }

  // ---- ambient pad -------------------------------------------------------
  function startAmbient() {
    var c = ensureCtx(); if (!c || ambient) return;
    if (c.state === "suspended") c.resume();

    // bus with a slow filter sweep
    var bus = c.createGain();
    bus.gain.value = 0.0;
    var filter = c.createBiquadFilter();
    filter.type = "lowpass";
    filter.frequency.value = 400;
    filter.Q.value = 6;
    bus.connect(filter); filter.connect(master);

    // a few detuned oscillators an octave+ fifth apart — deep drone
    var freqs = [55, 55.3, 82.5, 110, 110.4];
    var oscs = freqs.map(function (f) {
      var o = c.createOscillator();
      o.type = "sawtooth";
      o.frequency.value = f;
      o.detune.value = (Math.random() - 0.5) * 12;
      var g = c.createGain(); g.gain.value = 0.13;
      o.connect(g); g.connect(bus);
      o.start();
      return { o: o, g: g };
    });

    // slow LFO on the filter cutoff for a breathing, evolving timbre
    var lfo = c.createOscillator();
    lfo.frequency.value = 0.06;
    var lfoGain = c.createGain(); lfoGain.gain.value = 220;
    lfo.connect(lfoGain); lfoGain.connect(filter.frequency);
    lfo.start();

    // fade in
    bus.gain.linearRampToValueAtTime(0.35, c.currentTime + 3.0);

    ambient = { bus: bus, filter: filter, oscs: oscs, lfo: lfo, lfoGain: lfoGain };
  }

  function stopAmbient() {
    if (!ctx || !ambient) return;
    var c = ctx;
    ambient.bus.gain.linearRampToValueAtTime(0, c.currentTime + 0.6);
    setTimeout(function () {
      try {
        ambient.oscs.forEach(function (x) { x.o.stop(); });
        ambient.lfo.stop();
        ambient.bus.disconnect();
      } catch (e) {}
      ambient = null;
    }, 800);
  }

  function setAmbientVolume(v) {
    if (ambient) ambient.bus.gain.linearRampToValueAtTime(v, ctx.currentTime + 0.2);
  }

  // ---- SFX ---------------------------------------------------------------
  function sfx(name) {
    if (!enabled) return;
    var c = ensureCtx(); if (!c) return;
    if (c.state === "suspended") c.resume();
    var now = c.currentTime;

    function tone(freq, dur, type, gain, glideTo) {
      type = type || "sine"; gain = gain || 0.2;
      var o = c.createOscillator();
      o.type = type;
      o.frequency.setValueAtTime(freq, now);
      if (glideTo) o.frequency.exponentialRampToValueAtTime(glideTo, now + dur);
      var g = c.createGain();
      g.gain.setValueAtTime(0, now);
      g.gain.linearRampToValueAtTime(gain, now + 0.01);
      g.gain.exponentialRampToValueAtTime(0.0001, now + dur);
      o.connect(g); g.connect(master);
      o.start(now); o.stop(now + dur + 0.05);
    }

    switch (name) {
      case "hover":   tone(880, 0.08, "sine", 0.06); break;
      case "select":  tone(660, 0.12, "triangle", 0.12, 990); break;
      case "shutter": tone(1200, 0.05, "square", 0.1); setTimeout(function(){tone(800,0.06,"square",0.08);},50); break;
      case "record":  tone(440, 0.15, "sawtooth", 0.1, 220); break;
      case "stop":    tone(220, 0.2, "sawtooth", 0.1, 110); break;
      case "error":   tone(200, 0.3, "square", 0.15, 150); break;
      case "warp":    tone(110, 0.6, "sine", 0.18, 880); break;
    }
  }

  // ---- public toggle -----------------------------------------------------
  function enable() {
    enabled = true;
    localStorage.setItem("cosmos.sound", "1");
    startAmbient();
  }
  function disable() {
    enabled = false;
    localStorage.setItem("cosmos.sound", "0");
    stopAmbient();
  }
  function toggle() {
    if (enabled) disable(); else enable();
    return enabled;
  }
  // restore persisted preference (deferred until first gesture)
  function restore() {
    if (localStorage.getItem("cosmos.sound") === "1") {
      // can't start audio without a gesture; arm a one-shot resume
      enabled = true;
    }
  }
  restore();

  global.COSMOS_AUDIO = {
    enable: enable, disable: disable, toggle: toggle,
    get enabled() { return enabled; },
    sfx: sfx,
    setAmbientVolume: setAmbientVolume,
    // call from the first click anywhere to satisfy autoplay policy
    unlock: function () {
      if (enabled) { startAmbient(); }
      // also resume the context if it was created suspended
      if (ctx && ctx.state === "suspended") ctx.resume();
    }
  };
})(window);
