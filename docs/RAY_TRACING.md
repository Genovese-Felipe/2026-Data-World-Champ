# Graphics & Ray-Tracing Model

COSMOS renders a real-time solar system in the browser with [three.js](https://threejs.org) (WebGL). This doc explains the lighting and shading model — which borrows the *families of techniques* taught by the open ray-tracing education canon the project's references point to — and how each visual element is built.

## Reference lineage

The project's commission linked to a large set of graphics-education resources. The most directly influential to this implementation:

- **Ray Tracing in One Weekend** (Peter Shirley) and the [RayTracing.github.io](https://raytracing.github.io/) series — the foundational mental model: a *ray* carries light from a source, bounces off surfaces, and accumulates radiance. COSMOS uses the same conceptual primitives (a point light source, surface BRDFs, fresnel rim terms) though realized through WebGL's rasterization + shaders rather than a per-pixel path tracer.
- **[Scratchapixel](https://scratchapixel.com/)** — the noise/fbm techniques used in the Sun shader come straight from their procedural-texture lessons.
- **The Cherno** — the discipline of building a renderer incrementally, validating each stage, mirrors the structured approach in his graphics series.

True path-traced images (a la *Ray Tracing in One Weekend*) are too costly for a 60 fps browser scene with dozens of objects. The pragmatic translation: **physically-based surface shading lit by a real moving light**, plus **procedural fragment shaders** that approximate phenomena a full tracer would render — emission noise on the Sun, fresnel glow, and banding on gas giants.

---

## The Sun: a procedural emission shader

The Sun is the visual and physical centre of the scene. Rather than a flat emissive texture, it uses a custom `ShaderMaterial` (GLSL) that synthesises a churning photosphere:

```glsl
// 5-octave fractal Brownian motion (Scratchapixel-style hash noise)
float fbm(vec3 p){
  float v = 0.0, a = 0.5;
  for (int i = 0; i < 5; i++) { v += a * noise(p); p *= 2.0; a *= 0.5; }
  return v;
}
void main(){
  vec3 p = normalize(vPos) * 3.0 + vec3(uTime * 0.1);   // sample point drifts over time
  float n = fbm(p);                                     // churning convection cells
  vec3 col = mix(vec3(0.9,0.3,0.05), vec3(1.0,0.9,0.4), n);  // cool→hot
  float rim = pow(1.0 - abs(dot(normalize(vNormal), vec3(0,0,1))), 2.0);  // fresnel
  col += rim * vec3(1.0, 0.6, 0.1);                     // glowing limb
  gl_FragColor = vec4(col * 1.4, 1.0);
}
```

- The `uTime` uniform animates the noise coordinates every frame, so the surface genuinely churns.
- A **fresnel rim term** brightens the silhouette edge — the same effect a path tracer would produce from grazing-angle light — giving the sphere a glowing limb rather than a hard circle.
- An additive **glow sprite** (a radial-gradient canvas texture with `AdditiveBlending`) surrounds the Sun, approximating the corona's soft falloff that a volumetric tracer would compute.

---

## Planet lighting: physical light-to-surface

Every planet uses `MeshStandardMaterial`, three.js's physically-based material, lit by a single **`PointLight` parented to the Sun**. This is the rasterized analogue of the *light→surface→eye* ray in path tracing:

| Term | Path-tracing concept | COSMOS realization |
|---|---|---|
| **Diffuse** (Lambert) | `max(0, dot(N, L))` irradiance | Built into `MeshStandardMaterial`'s BRDF |
| **Specular** (Cook-Torrance-ish microfacet) | View-dependent highlight | `roughness` / `metalness` params per body |
| **Fresnel rim** | Grazing-angle reflectance boost | The Sun shader's explicit rim term |
| **Emission** | Radiance leaving a surface without incoming light | `emissive` = body colour × 0.04 (so dark sides aren't pure black) |

Because the Sun moves through the scene (the planets orbit it, and it sits at origin), each planet's lit hemisphere genuinely tracks the light source — the terminator sweeps as the planet rotates, exactly as it would in a tracer.

`renderer.shadowMap.enabled = true` (on High/Medium) lets planets and moons cast and receive real shadow maps — a cheap approximation of the occlusion rays a path tracer casts.

---

## Procedural textures (no image assets)

Every body's surface is generated on a `<canvas>` at runtime and uploaded as a `CanvasTexture`. This keeps the app asset-free and means each planet is a *synthesized* surface, not a photo:

| Body | Technique |
|---|---|
| **Mercury, Mars, Moon** | Rocky base colour + 8,000 noise grains + 60 radial-gradient "craters" (dark centre, bright rim) |
| **Venus** | Smoother rocky base, fewer craters (thick atmosphere) |
| **Earth** | Hand-placed elliptical landmass radial-gradients (green) over an ocean blue; white noise "clouds"; polar ice caps |
| **Jupiter, Saturn, Uranus, Neptune** | Horizontal band strips with sinusoidal shading + elliptical turbulence swirls per band |

---

## Saturn's rings: a ring-shader

Saturn's rings are a `RingGeometry` with custom UVs (radial) and a shader that synthesises banded ice/rock with **gap rings** — the Cassini-division-style dark bands that a tracer would render from varying particle density:

```glsl
float u = vUv.x;                  // 0 = inner, 1 = outer
float bands = 0.0;
for (int i = 0; i < 6; i++) bands += hash(floor(u * float(i+1) * 8.0)) * 0.5;
if (u > 0.4 && u < 0.45) a *= 0.15;   // gap
if (u > 0.7 && u < 0.73) a *= 0.2;   // gap
```

---

## Starfield

A `BufferGeometry` of up to 6,000 points (scaled by quality preset) distributed on a large sphere shell, with per-vertex colours biased toward white with occasional blue and warm stars. Points use `sizeAttenuation` so nearer stars appear larger.

---

## Quality presets

Because the scene must run from a phone to an 8K workstation, fidelity is scaled by `COSMOS_SCENE.setQuality(key)`:

| Preset | DPR cap | Stars | Sun/planet segments | Shadows | Shadow map |
|---|---|---|---|---|---|
| **High** | 2.0 | 6,000 | 64 | yes | 2048 |
| **Medium** | 1.5 | 3,000 | 32 | yes | 1024 |
| **Low** | 1.0 | 1,200 | 16 | no | 512 |

Setting a new quality disposes and rebuilds the scene at the new parameters, so the change is immediate and consistent.

---

## Why not a full path tracer?

A complete Monte-Carlo path tracer (the kind *Ray Tracing in One Weekend* walks through) in a browser at interactive framerates is possible only for very simple scenes — typically via a WebGPU compute shader or a heavily-denoised WebGL implementation. For a scene with ~10 light-emitting/reflecting bodies, an orbiting moon, rings, and a 6,000-star field, real-time PBR shading + procedural emission shaders is the pragmatic translation of the same *physics-first* philosophy: light from a real source, real surface interactions, real shadows. The visual *language* of the references is honoured; the *engine* is the one the browser gives us at 60 fps.
