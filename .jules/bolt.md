## 2026-07-11 - Costly Synchronous DOM Access in Iteration

**Learning:** `getComputedStyle` is an expensive DOM operation that calculates all styles for an element. When called synchronously inside a large loop, such as rendering hundreds of grid items, it causes significant main thread blocking and jank. The previous `TEAMCOLOR` function in `index.html` fetched CSS variables dynamically for every single item.

**Action:** Memoize values derived from `getComputedStyle` using a cache map whenever they will be read repeatedly during a render cycle, especially in purely static setups without a modern reactive framework.
## 2026-07-24 - Optimize Rapid Mouseover Events
**Learning:** In a dense grid (300+ items), using `innerHTML` inside a `mouseover` event handler creates a measurable CPU overhead because it triggers synchronous HTML parsing on every rapid interaction. Also, failing to early-return when the same element is hovered causes redundant DOM updates.
**Action:** For high-frequency events like `mouseover`, avoid `innerHTML`. Use `textContent` or modify existing DOM nodes directly. Always check if the target has actually changed before updating the DOM.

## 2026-08-01 - Avoid Object Instantiation in Render Loops
**Learning:** Instantiating objects (like `THREE.Vector3` or calling `Object.keys().forEach`) directly inside `requestAnimationFrame` creates unnecessary garbage collection pressure every frame, leading to micro-stutters and jank. The GC runs more frequently as arrays and objects are rapidly created and discarded.
**Action:** Pre-allocate frequently used objects (like vectors for calculations) at module or class scope. Pre-compute and cache derived collections (like `activeBodies` or arrays of meshes) instead of generating them inside the tight render loop.
