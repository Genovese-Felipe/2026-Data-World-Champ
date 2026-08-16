/*
 * COSMOS — Image & video export pipeline
 * ---------------------------------------------------------------------------
 * Lets the user capture the live scene in multiple formats and resolutions,
 * fully client-side, no servers.
 *
 * Image export:
 *   • PNG (lossless) and JPEG (smaller) at the user's chosen resolution.
 *   • Resolutions: 1080p, 1440p, 4K (3840×2160), 8K (7680×4320).
 *   • Implemented by temporarily resizing the WebGL drawing buffer through
 *     COSMOS_SCENE.getScreenshot(w,h), which re-renders at the target size
 *     and returns a data URL — then triggers a download.
 *
 * Video recording:
 *   • Uses canvas.captureStream(fps) + MediaRecorder to capture the live
 *     animation loop as WebM (VP9/VP8, widely supported across browsers).
 *   • Exposes start/stop; on stop, assembles a Blob and downloads it.
 *   • MP4 is requested when supported (Safari); otherwise WebM.
 *
 * Public surface (window.COSMOS_EXPORT):
 *   COSMOS_EXPORT.image(format, width, height)   // format: 'png'|'jpeg'
 *   COSMOS_EXPORT.startVideo(fps)
 *   COSMOS_EXPORT.stopVideo()
 *   COSMOS_EXPORT.isRecording
 *   COSMOS_EXPORT.SUPPORTED
 */
(function (global) {
  "use strict";

  var recorder = null, chunks = [], recording = false, stream = null;

  function canvasSupportsToDataURL() {
    try {
      return typeof document !== "undefined" &&
        typeof document.createElement === "function" &&
        !!document.createElement("canvas").toDataURL;
    } catch (e) { return false; }
  }
  function canvasSupportsCaptureStream() {
    try {
      return typeof HTMLCanvasElement !== "undefined" &&
        typeof HTMLCanvasElement.prototype.captureStream === "function";
    } catch (e) { return false; }
  }
  var SUPPORTED = {
    image: canvasSupportsToDataURL(),
    video: canvasSupportsCaptureStream()
  };

  function downloadBlob(blob, filename) {
    var url = URL.createObjectURL(blob);
    var a = document.createElement("a");
    a.href = url; a.download = filename;
    document.body.appendChild(a); a.click();
    setTimeout(function () { URL.revokeObjectURL(url); a.remove(); }, 200);
  }

  function downloadDataUrl(dataUrl, filename) {
    var a = document.createElement("a");
    a.href = dataUrl; a.download = filename;
    document.body.appendChild(a); a.click();
    setTimeout(function () { a.remove(); }, 200);
  }

  function stamp() {
    var d = new Date();
    var p = function (n) { return String(n).padStart(2, "0"); };
    return d.getFullYear() + p(d.getMonth() + 1) + p(d.getDate()) + "-" +
           p(d.getHours()) + p(d.getMinutes()) + p(d.getSeconds());
  }

  // ---- image export ------------------------------------------------------
  function image(format, width, height) {
    if (!SUPPORTED.image) return Promise.reject(new Error("image export unsupported"));
    if (!global.COSMOS_SCENE) return Promise.reject(new Error("scene not ready"));
    format = format || "png";
    // clamp very large renders for safety; 8K = 7680×4320
    var w = Math.min(width || 1920, 8192);
    var h = Math.min(height || 1080, 8192);

    return global.COSMOS_SCENE.getScreenshot(w, h).then(function (dataUrl) {
      if (format === "jpeg") {
        // re-encode the PNG dataURL as JPEG at quality 0.92
        return new Promise(function (resolve) {
          var img = new Image();
          img.onload = function () {
            var c = document.createElement("canvas");
            c.width = w; c.height = h;
            var ctx = c.getContext("2d");
            ctx.fillStyle = "#000"; ctx.fillRect(0, 0, w, h);
            ctx.drawImage(img, 0, 0, w, h);
            resolve(c.toDataURL("image/jpeg", 0.92));
          };
          img.src = dataUrl;
        });
      }
      return dataUrl;
    }).then(function (finalUrl) {
      var ext = format === "jpeg" ? "jpg" : "png";
      downloadDataUrl(finalUrl, "cosmos-" + stamp() + "-" + w + "x" + h + "." + ext);
      if (global.COSMOS_AUDIO) global.COSMOS_AUDIO.sfx("shutter");
      return finalUrl;
    });
  }

  // ---- video recording ---------------------------------------------------
  function startVideo(fps) {
    if (!SUPPORTED.video || recording) return false;
    if (!global.COSMOS_SCENE) return false;
    fps = fps || 30;
    var renderer = global.COSMOS_SCENE.getRenderer();
    if (!renderer) return false;

    stream = renderer.domElement.captureStream(fps);
    chunks = [];

    // pick the best supported mime type
    var types = [
      "video/webm;codecs=vp9",
      "video/webm;codecs=vp8",
      "video/webm",
      "video/mp4"
    ];
    var mimeType = "";
    for (var i = 0; i < types.length; i++) {
      if (window.MediaRecorder && MediaRecorder.isTypeSupported(types[i])) {
        mimeType = types[i]; break;
      }
    }
    try {
      recorder = new MediaRecorder(stream, mimeType ? { mimeType: mimeType, videoBitsPerSecond: 12000000 } : undefined);
    } catch (e) {
      try { recorder = new MediaRecorder(stream); }
      catch (e2) { return false; }
    }

    recorder.ondataavailable = function (e) {
      if (e.data && e.data.size > 0) chunks.push(e.data);
    };
    recorder.onstop = function () {
      var blob = new Blob(chunks, { type: mimeType || "video/webm" });
      var ext = (mimeType && mimeType.indexOf("mp4") >= 0) ? "mp4" : "webm";
      downloadBlob(blob, "cosmos-recording-" + stamp() + "." + ext);
      if (stream) { stream.getTracks().forEach(function (t) { t.stop(); }); stream = null; }
      if (global.COSMOS_AUDIO) global.COSMOS_AUDIO.sfx("stop");
    };

    recorder.start();
    recording = true;
    if (global.COSMOS_AUDIO) global.COSMOS_AUDIO.sfx("record");
    return true;
  }

  function stopVideo() {
    if (!recording || !recorder) return false;
    recorder.stop();
    recording = false;
    return true;
  }

  global.COSMOS_EXPORT = {
    image: image,
    startVideo: startVideo,
    stopVideo: stopVideo,
    get isRecording() { return recording; },
    SUPPORTED: SUPPORTED
  };
})(window);
