## 2026-07-11 - Costly Synchronous DOM Access in Iteration

**Learning:** `getComputedStyle` is an expensive DOM operation that calculates all styles for an element. When called synchronously inside a large loop, such as rendering hundreds of grid items, it causes significant main thread blocking and jank. The previous `TEAMCOLOR` function in `index.html` fetched CSS variables dynamically for every single item.

**Action:** Memoize values derived from `getComputedStyle` using a cache map whenever they will be read repeatedly during a render cycle, especially in purely static setups without a modern reactive framework.
## 2026-07-24 - Optimize Rapid Mouseover Events
**Learning:** In a dense grid (300+ items), using `innerHTML` inside a `mouseover` event handler creates a measurable CPU overhead because it triggers synchronous HTML parsing on every rapid interaction. Also, failing to early-return when the same element is hovered causes redundant DOM updates.
**Action:** For high-frequency events like `mouseover`, avoid `innerHTML`. Use `textContent` or modify existing DOM nodes directly. Always check if the target has actually changed before updating the DOM.
## 2026-10-21 - Three.js Render Loop Garbage Collection

**Learning:** Object allocation (e.g., `new THREE.Vector3()`) and iteration methods that construct temporary arrays (like `Object.keys(bodyMeshes).forEach(...)`) inside a 60FPS `requestAnimationFrame` loop cause immense memory churn. This forces the V8 garbage collector to work continuously, eventually leading to noticeable frame drops (jank) in smooth animations.
**Action:** Always pre-allocate arrays mapping keys to objects right after initialization if the object pool is static. Lift invariant object instantiations outside the render loop and reuse them using `.set()` or similar mutation methods instead of `new`.
