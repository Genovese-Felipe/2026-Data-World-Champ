## 2026-07-11 - Costly Synchronous DOM Access in Iteration

**Learning:** `getComputedStyle` is an expensive DOM operation that calculates all styles for an element. When called synchronously inside a large loop, such as rendering hundreds of grid items, it causes significant main thread blocking and jank. The previous `TEAMCOLOR` function in `index.html` fetched CSS variables dynamically for every single item.

**Action:** Memoize values derived from `getComputedStyle` using a cache map whenever they will be read repeatedly during a render cycle, especially in purely static setups without a modern reactive framework.
## 2026-07-24 - Optimize Rapid Mouseover Events
**Learning:** In a dense grid (300+ items), using `innerHTML` inside a `mouseover` event handler creates a measurable CPU overhead because it triggers synchronous HTML parsing on every rapid interaction. Also, failing to early-return when the same element is hovered causes redundant DOM updates.
**Action:** For high-frequency events like `mouseover`, avoid `innerHTML`. Use `textContent` or modify existing DOM nodes directly. Always check if the target has actually changed before updating the DOM.
## 2024-05-18 - Avoid Garbage Collection in Render Loop
**Learning:** In the Three.js codebase, instantiating new objects (like `new THREE.Vector3`) and creating arrays dynamically (like using `Object.keys(bodyMeshes)`) inside the `requestAnimationFrame` render loop (`animate()`) creates excessive garbage collection pressure, leading to frame drops.
**Action:** Always extract constant vector instantiations into module-scope variables, reuse vectors by updating them in-place with `.set()`, and use pre-allocated cached arrays for iteration inside critical loops to ensure stable frame rates.
