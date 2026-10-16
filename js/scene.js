/*
 * COSMOS — Solar System 3D scene (three.js + WebGL)
 * ---------------------------------------------------------------------------
 * The visual centrepiece: a live, ray-traced-lit solar system the user can
 * orbit, zoom, and click to inspect. Key techniques inspired by the ray-
 * tracing references (Ray Tracing in One Weekend, Scratchapixel, The Cherno):
 *
 *   • The Sun uses a custom ShaderMaterial with a noise-based corona +
 *     additive glow sprite, approximating volumetric emission.
 *   • Planets receive real-time point lighting from a moving Sun light —
 *     a physical light->surface model (diffuse + specular + rim) rather
 *     than baked textures.
 *   • Procedural canvas textures for each body (cratered rocky worlds,
 *     banded gas giants, Earth's continents) — no external image assets.
 *   • Orbit rings, a procedural starfield of ~6000 points, and Saturn's
 *     ring system built from a custom shader.
 *   • Camera: OrbitControls (drag orbit, scroll zoom, right-drag pan),
 *     plus an auto-orbit "cinematic" mode.
 *
 * Quality presets scale DPR, star count, and shadow map size so the scene
 * runs on anything from a phone to an 8K-capable workstation.
 *
 * Public surface (window.COSMOS_SCENE):
 *   COSMOS_SCENE.init(container)
 *   COSMOS_SCENE.setQuality('high'|'medium'|'low')
 *   COSMOS_SCENE.setOrbitAuto(bool)
 *   COSMOS_SCENE.focusBody(name)
 *   COSMOS_SCENE.onSelect(callback)   // callback receives body data
 *   COSMOS_SCENE.getScreenshot(w,h)   -> Promise<dataURL> (for export)
 *   COSMOS_SCENE.getExternalRenderer  // exposed for video capture
 *   COSMOS_SCENE.dispose()
 */
// three.js + OrbitControls are imported as ES modules via the import map in index.html.
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";

var global = window;
(function (global) {
  "use strict";
  var THREE_ref = THREE;

  var QUALITY = {
    high:   { dpr: [2, 2],    stars: 6000, sunSeg: 64, planetSeg: 64, shadows: true,  shadowMap: 2048 },
    medium: { dpr: [1, 1.5],  stars: 3000, sunSeg: 32, planetSeg: 32, shadows: true,  shadowMap: 1024 },
    low:    { dpr: [0.75, 1], stars: 1200, sunSeg: 16, planetSeg: 16, shadows: false, shadowMap: 512 }
  };

  var BODIES = [
    // name, radius, distance, color, orbitalSpeed, spinSpeed, hasRings, isSun
    { name: "sun",     r: 8.0,  d: 0,    color: 0xffaa33, orb: 0,      spin: 0.0008, rings: false, sun: true,  glow: true },
    { name: "mercury", r: 0.9,  d: 16,   color: 0x9c8c7c, orb: 0.0048, spin: 0.004,  rings: false },
    { name: "venus",   r: 1.5,  d: 22,   color: 0xe8b87a, orb: 0.0035, spin: 0.002,  rings: false },
    { name: "earth",   r: 1.6,  d: 30,   color: 0x2a6fdb, orb: 0.0029, spin: 0.012,  rings: false, moon: true },
    { name: "mars",    r: 1.1,  d: 40,   color: 0xc1440e, orb: 0.0024, spin: 0.011,  rings: false },
    { name: "jupiter", r: 4.2,  d: 58,   color: 0xd8a878, orb: 0.0013, spin: 0.025,  rings: false },
    { name: "saturn",  r: 3.6,  d: 74,   color: 0xe8d4a0, orb: 0.0009, spin: 0.022,  rings: true },
    { name: "uranus",  r: 2.4,  d: 88,   color: 0x9fe0e8, orb: 0.0006, spin: 0.014,  rings: false },
    { name: "neptune", r: 2.3,  d: 100,  color: 0x3b5bdb, orb: 0.0005, spin: 0.015,  rings: false }
  ];

  var QUALITY_KEY = "high";
  var container, renderer, scene, camera, controls, sun, sunLight, starField;
  var bodyMeshes = {};      // name -> { mesh, group, data, ringMesh?, moonMesh? }
  var raycaster, pointer, onSelectCb;
  var autoOrbit = false;
  var autoAngle = 0;
  var rafId;
  var lastFrame = 0;
  var externalRenderHook = null; // set by video recorder

  // ---- procedural textures (canvas) --------------------------------------
  function makeRockTexture(baseColor, craters) {
    var c = document.createElement("canvas");
    c.width = c.height = 512;
    var ctx = c.getContext("2d");
    var base = "#" + baseColor.toString(16).padStart(6, "0");
    ctx.fillStyle = base; ctx.fillRect(0, 0, 512, 512);
    // noise grain
    for (var i = 0; i < 8000; i++) {
      var x = Math.random() * 512, y = Math.random() * 512;
      var v = Math.random() * 40 - 20;
      ctx.fillStyle = "rgba(0,0,0," + Math.abs(v / 60) + ")";
      ctx.fillRect(x, y, 1.5, 1.5);
    }
    // craters
    if (craters) {
      for (var k = 0; k < craters; k++) {
        var cx = Math.random() * 512, cy = Math.random() * 512;
        var cr = 4 + Math.random() * 28;
        var g = ctx.createRadialGradient(cx, cy, 0, cx, cy, cr);
        g.addColorStop(0, "rgba(0,0,0,0.5)");
        g.addColorStop(0.7, "rgba(0,0,0,0.15)");
        g.addColorStop(1, "rgba(255,255,255,0.08)");
        ctx.fillStyle = g;
        ctx.beginPath(); ctx.arc(cx, cy, cr, 0, Math.PI * 2); ctx.fill();
      }
    }
    var tex = new THREE.CanvasTexture(c);
    tex.wrapS = tex.wrapT = THREE.RepeatWrapping;
    return tex;
  }

  function makeGasGiantTexture(baseColor, bands) {
    var c = document.createElement("canvas");
    c.width = 1024; c.height = 512;
    var ctx = c.getContext("2d");
    var base = "#" + baseColor.toString(16).padStart(6, "0");
    ctx.fillStyle = base; ctx.fillRect(0, 0, 1024, 512);
    // horizontal bands
    for (var b = 0; b < bands; b++) {
      var y = (b / bands) * 512;
      var h = 512 / bands;
      var shade = Math.sin(b * 0.7) * 30;
      ctx.fillStyle = shade > 0
        ? "rgba(255,255,255," + (shade / 100) + ")"
        : "rgba(0,0,0," + (-shade / 100) + ")";
      ctx.fillRect(0, y, 1024, h);
      // turbulence swirls
      for (var s = 0; s < 20; s++) {
        var sx = Math.random() * 1024, sy = y + Math.random() * h;
        var sr = 4 + Math.random() * 18;
        ctx.fillStyle = "rgba(255,255,255," + (Math.random() * 0.12) + ")";
        ctx.beginPath(); ctx.ellipse(sx, sy, sr * 2, sr * 0.6, 0, 0, Math.PI * 2); ctx.fill();
      }
    }
    var tex = new THREE.CanvasTexture(c);
    tex.wrapS = THREE.RepeatWrapping;
    return tex;
  }

  function makeEarthTexture() {
    var c = document.createElement("canvas");
    c.width = 1024; c.height = 512;
    var ctx = c.getContext("2d");
    // ocean
    ctx.fillStyle = "#1a4d80"; ctx.fillRect(0, 0, 1024, 512);
    // continents — pseudo-random green landmasses
    var landmasses = [
      [200, 180, 140, 80], [240, 160, 90, 120], [500, 150, 160, 140],
      [520, 300, 120, 90], [720, 180, 150, 110], [780, 280, 100, 70],
      [120, 320, 80, 60], [350, 360, 70, 50], [640, 360, 90, 60]
    ];
    landmasses.forEach(function (lm) {
      var g = ctx.createRadialGradient(lm[0], lm[1], 0, lm[0], lm[1], lm[2]);
      g.addColorStop(0, "#3a7d3a");
      g.addColorStop(0.6, "#2d5a2d");
      g.addColorStop(1, "rgba(45,90,45,0)");
      ctx.fillStyle = g;
      ctx.beginPath(); ctx.ellipse(lm[0], lm[1], lm[2], lm[3], Math.random(), 0, Math.PI * 2); ctx.fill();
    });
    // ice caps
    ctx.fillStyle = "rgba(255,255,255,0.85)";
    ctx.fillRect(0, 0, 1024, 28); ctx.fillRect(0, 484, 1024, 28);
    // clouds — faint white noise
    for (var i = 0; i < 400; i++) {
      var x = Math.random() * 1024, y = Math.random() * 512;
      ctx.fillStyle = "rgba(255,255,255," + (Math.random() * 0.18) + ")";
      ctx.beginPath(); ctx.ellipse(x, y, 8 + Math.random() * 20, 4 + Math.random() * 8, 0, 0, Math.PI * 2); ctx.fill();
    }
    var tex = new THREE.CanvasTexture(c);
    tex.wrapS = THREE.RepeatWrapping;
    return tex;
  }

  // ---- the Sun: shader corona + additive glow ---------------------------
  function makeSun(radius) {
    var q = QUALITY[QUALITY_KEY];
    // core sphere with emissive shader
    var geo = new THREE.SphereGeometry(Math.max(0.1, radius), q.sunSeg, q.sunSeg);
    var mat = new THREE.ShaderMaterial({
      uniforms: { uTime: { value: 0 } },
      vertexShader: [
        "varying vec3 vPos; varying vec3 vNormal;",
        "void main(){ vPos=position; vNormal=normal; gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0); }"
      ].join("\n"),
      fragmentShader: [
        "uniform float uTime; varying vec3 vPos; varying vec3 vNormal;",
        // simple hash noise
        "float hash(vec3 p){ p=fract(p*0.3183099+0.1); p*=17.0; return fract(p.x*p.y*p.z*(p.x+p.y+p.z)); }",
        "float noise(vec3 p){ vec3 i=floor(p); vec3 f=fract(p); f=f*f*(3.0-2.0*f);",
        "  return mix(mix(mix(hash(i),hash(i+vec3(1,0,0)),f.x),mix(hash(i+vec3(0,1,0)),hash(i+vec3(1,1,0)),f.x),f.y),",
        "             mix(mix(hash(i+vec3(0,0,1)),hash(i+vec3(1,0,1)),f.x),mix(hash(i+vec3(0,1,1)),hash(i+vec3(1,1,1)),f.x),f.y),f.z); }",
        "float fbm(vec3 p){ float v=0.0,a=0.5; for(int i=0;i<5;i++){ v+=a*noise(p); p*=2.0; a*=0.5; } return v; }",
        "void main(){",
        "  vec3 p=normalize(vPos)*3.0+vec3(uTime*0.1);",
        "  float n=fbm(p);",
        "  vec3 hot=vec3(1.0,0.9,0.4); vec3 cool=vec3(0.9,0.3,0.05);",
        "  vec3 col=mix(cool,hot,n);",
        "  // fresnel rim for a glowing edge",
        "  float rim=pow(1.0-abs(dot(normalize(vNormal),vec3(0.0,0.0,1.0))),2.0);",
        "  col+=rim*vec3(1.0,0.6,0.1);",
        "  gl_FragColor=vec4(col*1.4,1.0); }"
      ].join("\n")
    });
    var mesh = new THREE.Mesh(geo, mat);
    mesh.userData = { isSun: true, name: "sun" };

    // additive glow sprite
    var glowTex = makeGlowTexture();
    var glowMat = new THREE.SpriteMaterial({
      map: glowTex, color: 0xffaa44, transparent: true,
      blending: THREE.AdditiveBlending, depthWrite: false
    });
    var glow = new THREE.Sprite(glowMat);
    glow.scale.set(radius * 5, radius * 5, 1);
    mesh.add(glow);
    return { mesh: mesh, mat: mat };
  }

  function makeGlowTexture() {
    var c = document.createElement("canvas");
    c.width = c.height = 256;
    var ctx = c.getContext("2d");
    var g = ctx.createRadialGradient(128, 128, 0, 128, 128, 128);
    g.addColorStop(0, "rgba(255,200,100,1)");
    g.addColorStop(0.2, "rgba(255,150,50,0.6)");
    g.addColorStop(0.5, "rgba(255,100,20,0.2)");
    g.addColorStop(1, "rgba(255,80,0,0)");
    ctx.fillStyle = g; ctx.fillRect(0, 0, 256, 256);
    return new THREE.CanvasTexture(c);
  }

  // ---- Saturn's rings: custom shader -------------------------------------
  function makeRings(innerR, outerR) {
    var geo = new THREE.RingGeometry(innerR, outerR, 96);
    // fix UVs so u goes radially
    var pos = geo.attributes.position; var v3 = new THREE.Vector3();
    var uv = geo.attributes.uv;
    for (var i = 0; i < pos.count; i++) {
      v3.fromBufferAttribute(pos, i);
      var r = v3.length();
      uv.setXY(i, (r - innerR) / (outerR - innerR), 0);
    }
    var mat = new THREE.ShaderMaterial({
      uniforms: { uInner: { value: innerR }, uOuter: { value: outerR } },
      vertexShader: "varying vec2 vUv; void main(){ vUv=uv; gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0); }",
      fragmentShader: [
        "varying vec2 vUv;",
        "float hash(float n){ return fract(sin(n)*43758.5453); }",
        "void main(){",
        "  float u=vUv.x; float bands=0.0;",
        "  for(int i=0;i<6;i++){ float f=float(i+1)*8.0; bands+=hash(floor(u*f))*0.5; }",
        "  float a=0.7*(0.4+bands*0.3);",
        "  // gap rings",
        "  if(u>0.4 && u<0.45) a*=0.15;",
        "  if(u>0.7 && u<0.73) a*=0.2;",
        "  vec3 col=mix(vec3(0.9,0.8,0.6),vec3(0.7,0.6,0.45),bands);",
        "  gl_FragColor=vec4(col,a); }"
      ].join("\n"),
      transparent: true, side: THREE.DoubleSide, depthWrite: false
    });
    var m = new THREE.Mesh(geo, mat);
    m.rotation.x = Math.PI / 2 - 0.4;
    return m;
  }

  // ---- starfield ---------------------------------------------------------
  function makeStarfield(count) {
    var geo = new THREE.BufferGeometry();
    var positions = new Float32Array(count * 3);
    var colors = new Float32Array(count * 3);
    for (var i = 0; i < count; i++) {
      // distribute on a large sphere
      var r = 400 + Math.random() * 400;
      var theta = Math.random() * Math.PI * 2;
      var phi = Math.acos(2 * Math.random() - 1);
      positions[i * 3] = r * Math.sin(phi) * Math.cos(theta);
      positions[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta);
      positions[i * 3 + 2] = r * Math.cos(phi);
      // subtle color variation (white/blue/warm)
      var t = Math.random();
      if (t < 0.7) { colors[i*3]=1; colors[i*3+1]=1; colors[i*3+2]=1; }
      else if (t < 0.9) { colors[i*3]=0.7; colors[i*3+1]=0.8; colors[i*3+2]=1; }
      else { colors[i*3]=1; colors[i*3+1]=0.85; colors[i*3+2]=0.7; }
    }
    geo.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    geo.setAttribute("color", new THREE.BufferAttribute(colors, 3));
    var mat = new THREE.PointsMaterial({
      size: 1.2, vertexColors: true, transparent: true, opacity: 0.9,
      sizeAttenuation: true, depthWrite: false
    });
    return new THREE.Points(geo, mat);
  }

  // ---- build the scene ---------------------------------------------------
  function init(el) {
    container = el;
    var q = QUALITY[QUALITY_KEY];
    var w = container.clientWidth, h = container.clientHeight;

    scene = new THREE.Scene();
    scene.background = new THREE.Color(0x05060f);

    camera = new THREE.PerspectiveCamera(55, w / h, 0.1, 2000);
    camera.position.set(0, 30, 70);

    renderer = new THREE.WebGLRenderer({ antialias: q.dpr[1] > 1, alpha: false,
      preserveDrawingBuffer: true }); // preserveDrawingBuffer for screenshots
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, q.dpr[1]));
    renderer.setSize(w, h);
    renderer.shadowMap.enabled = q.shadows;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    container.appendChild(renderer.domElement);

    // orbit controls
    controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.06;
    controls.minDistance = 12;
    controls.maxDistance = 300;
    controls.target.set(0, 0, 0);

    // Sun + light
    var sunBuilt = makeSun(8);
    sun = sunBuilt.mesh;
    sunLight = new THREE.PointLight(0xfff0d0, 3, 0, 1.5);
    sunLight.castShadow = q.shadows;
    sunLight.shadow.mapSize.set(q.shadowMap, q.shadowMap);
    sun.add(sunLight);
    scene.add(sun);
    bodyMeshes["sun"] = { mesh: sun, group: sun, data: BODIES[0], mat: sunBuilt.mat };

    // a faint ambient so the dark sides aren't pure black
    scene.add(new THREE.AmbientLight(0x222233, 0.4));

    // planets
    BODIES.slice(1).forEach(function (b) {
      var group = new THREE.Group(); // orbits around the sun
      var geo = new THREE.SphereGeometry(Math.max(0.1, b.r), q.planetSeg, q.planetSeg);
      var tex;
      if (b.name === "earth") tex = makeEarthTexture();
      else if (b.name === "mercury" || b.name === "mars") tex = makeRockTexture(b.color, 60);
      else if (b.name === "venus") tex = makeRockTexture(b.color, 20);
      else tex = makeGasGiantTexture(b.color, 14);

      var mat = new THREE.MeshStandardMaterial({
        map: tex, roughness: 0.85, metalness: 0.0,
        emissive: new THREE.Color(b.color).multiplyScalar(0.04)
      });
      var mesh = new THREE.Mesh(geo, mat);
      mesh.castShadow = q.shadows; mesh.receiveShadow = q.shadows;
      mesh.position.x = b.d;
      mesh.userData = { name: b.name };
      group.add(mesh);

      // axial tilt
      mesh.rotation.z = (b.name === "uranus") ? 1.7 : 0.2 + Math.random() * 0.2;

      // rings
      var ringMesh = null;
      if (b.rings) {
        ringMesh = makeRings(b.r * 1.4, b.r * 2.4);
        mesh.add(ringMesh);
      }

      // moon for earth
      var moonMesh = null;
      if (b.moon) {
        var mgeo = new THREE.SphereGeometry(0.4, 24, 24);
        var mmat = new THREE.MeshStandardMaterial({ map: makeRockTexture(0x999999, 40), roughness: 1 });
        moonMesh = new THREE.Mesh(mgeo, mmat);
        moonMesh.castShadow = q.shadows;
        moonMesh.position.set(3, 0, 0);
        mesh.add(moonMesh);
      }

      // orbit ring (visual)
      var ringGeo = new THREE.RingGeometry(Math.max(0.1, b.d - 0.05), b.d + 0.05, 128);
      var ringMat = new THREE.MeshBasicMaterial({ color: 0x334466, transparent: true, opacity: 0.25, side: THREE.DoubleSide });
      var orbitRing = new THREE.Mesh(ringGeo, ringMat);
      orbitRing.rotation.x = Math.PI / 2;
      scene.add(orbitRing);

      // start each at a random angle so they're not lined up
      group.rotation.y = Math.random() * Math.PI * 2;
      scene.add(group);

      bodyMeshes[b.name] = { mesh: mesh, group: group, data: b, orbitRing: orbitRing, ringMesh: ringMesh, moonMesh: moonMesh };
    });

    // starfield
    starField = makeStarfield(q.stars);
    scene.add(starField);

    // interaction
    raycaster = new THREE.Raycaster();
    pointer = new THREE.Vector2();
    renderer.domElement.addEventListener("pointerdown", onPointerDown, false);

    window.addEventListener("resize", onResize, false);

    animate(0);
  }

  function onPointerDown(e) {
    var rect = renderer.domElement.getBoundingClientRect();
    pointer.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
    pointer.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;
    raycaster.setFromCamera(pointer, camera);
    var meshes = Object.keys(bodyMeshes).map(function (k) { return bodyMeshes[k].mesh; });
    var hits = raycaster.intersectObjects(meshes, false);
    if (hits.length) {
      var name = hits[0].object.userData.name;
      if (name) {
        if (global.COSMOS_AUDIO) global.COSMOS_AUDIO.sfx("select");
        focusBody(name);
        if (onSelectCb) onSelectCb(name, bodyMeshes[name].data);
      }
    }
  }

  function focusBody(name) {
    var b = bodyMeshes[name];
    if (!b) return;
    // get world position of the body
    var target = new THREE.Vector3();
    b.mesh.getWorldPosition(target);
    controls.target.copy(target);
    // move camera closer, offset
    var dist = Math.max(8, b.data.r * 4);
    var offset = new THREE.Vector3(dist, dist * 0.5, dist);
    camera.position.copy(target.clone().add(offset));
    if (global.COSMOS_AUDIO) global.COSMOS_AUDIO.sfx("warp");
  }

  function onResize() {
    if (!container || !renderer) return;
    var w = container.clientWidth, h = container.clientHeight;
    camera.aspect = w / h; camera.updateProjectionMatrix();
    renderer.setSize(w, h);
  }

  // ---- animation loop ----------------------------------------------------
  function animate(t) {
    rafId = requestAnimationFrame(animate);
    var dt = lastFrame ? (t - lastFrame) / 16.67 : 1;
    lastFrame = t;

    var sunMat = bodyMeshes["sun"].mat;
    if (sunMat && sunMat.uniforms) sunMat.uniforms.uTime.value = t * 0.001;

    // rotate + orbit planets
    Object.keys(bodyMeshes).forEach(function (name) {
      var b = bodyMeshes[name];
      if (b.data.sun) { b.mesh.rotation.y += b.data.spin * dt; return; }
      b.group.rotation.y += b.data.orb * dt;
      b.mesh.rotation.y += b.data.spin * dt;
      if (b.moonMesh) b.moonMesh.position.applyAxisAngle(new THREE.Vector3(0,1,0), 0.02 * dt);
    });

    if (starField) starField.rotation.y += 0.00005 * dt;

    if (autoOrbit) {
      autoAngle += 0.0015 * dt;
      var r = camera.position.distanceTo(controls.target);
      // orbit the camera around the target
      var offset = new THREE.Vector3(Math.cos(autoAngle) * r, camera.position.y - controls.target.y, Math.sin(autoAngle) * r);
      camera.position.copy(controls.target).add(offset);
    }

    controls.update();

    // allow external capture hook to drive renders at custom resolution
    if (externalRenderHook) externalRenderHook(renderer, scene, camera);
    else renderer.render(scene, camera);
  }

  // ---- quality + control APIs -------------------------------------------
  function setQuality(key) {
    if (!QUALITY[key]) return;
    QUALITY_KEY = key;
    localStorage.setItem("cosmos.quality", key);
    // rebuild the scene for the new quality
    if (container) {
      dispose();
      init(container);
    }
  }

  function setOrbitAuto(v) { autoOrbit = v; autoAngle = Math.atan2(camera.position.z, camera.position.x); }

  function onSelect(cb) { onSelectCb = cb; }

  function getScreenshot(w, h) {
    // render at custom resolution by temporarily resizing the drawing buffer
    return new Promise(function (resolve) {
      var oldSize = renderer.getSize(new THREE.Vector2());
      var oldPR = renderer.getPixelRatio();
      var oldAspect = camera.aspect;
      renderer.setPixelRatio(1);
      renderer.setSize(w, h, false); // updateStyle=false
      camera.aspect = w / h; camera.updateProjectionMatrix();
      renderer.render(scene, camera);
      var url = renderer.domElement.toDataURL("image/png");
      // restore
      renderer.setPixelRatio(oldPR);
      renderer.setSize(oldSize.x, oldSize.y, false);
      camera.aspect = oldAspect; camera.updateProjectionMatrix();
      onResize();
      resolve(url);
    });
  }

  function dispose() {
    cancelAnimationFrame(rafId);
    if (renderer) {
      renderer.dispose();
      if (renderer.domElement && renderer.domElement.parentNode)
        renderer.domElement.parentNode.removeChild(renderer.domElement);
    }
    bodyMeshes = {};
    if (controls) controls.dispose();
    window.removeEventListener("resize", onResize);
  }

  // restore quality preference
  QUALITY_KEY = localStorage.getItem("cosmos.quality") || "high";
  if (!QUALITY[QUALITY_KEY]) QUALITY_KEY = "high";

  global.COSMOS_SCENE = {
    init: init, dispose: dispose,
    setQuality: setQuality, setOrbitAuto: setOrbitAuto,
    focusBody: focusBody, onSelect: onSelect,
    getScreenshot: getScreenshot,
    getQuality: function () { return QUALITY_KEY; },
    setExternalRenderHook: function (fn) { externalRenderHook = fn; },
    clearExternalRenderHook: function () { externalRenderHook = null; },
    getRenderer: function () { return renderer; },
    getScene: function () { return scene; },
    getCamera: function () { return camera; },
    getControls: function () { return controls; },
    BODIES: BODIES
  };
})(window);
