## 2026-07-11 - Costly Synchronous DOM Access in Iteration

**Learning:** `getComputedStyle` is an expensive DOM operation that calculates all styles for an element. When called synchronously inside a large loop, such as rendering hundreds of grid items, it causes significant main thread blocking and jank. The previous `TEAMCOLOR` function in `index.html` fetched CSS variables dynamically for every single item.

**Action:** Memoize values derived from `getComputedStyle` using a cache map whenever they will be read repeatedly during a render cycle, especially in purely static setups without a modern reactive framework.
## 2026-07-24 - Optimize Rapid Mouseover Events
**Learning:** In a dense grid (300+ items), using `innerHTML` inside a `mouseover` event handler creates a measurable CPU overhead because it triggers synchronous HTML parsing on every rapid interaction. Also, failing to early-return when the same element is hovered causes redundant DOM updates.
**Action:** For high-frequency events like `mouseover`, avoid `innerHTML`. Use `textContent` or modify existing DOM nodes directly. Always check if the target has actually changed before updating the DOM.

## 2026-10-22 - Pre-allocating Objects in requestAnimationFrame

**Learning:** Creating new objects (like `THREE.Vector3` or anonymous functions) inside the `requestAnimationFrame` render loop causes significant garbage collection (GC) pressure, leading to frame drops and jank over time. Additionally, calling `Object.keys()` continuously in the loop performs unnecessary work that could be cached.

**Action:** Cache object keys into an array when the collection is updated, and use standard `for` loops to iterate over them. Always pre-allocate reusable vectors or objects at the module scope and update their values in-place (e.g., `.set()`) instead of instantiating new objects inside the render loop.
