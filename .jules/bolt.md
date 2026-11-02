## 2026-07-11 - Costly Synchronous DOM Access in Iteration

**Learning:** `getComputedStyle` is an expensive DOM operation that calculates all styles for an element. When called synchronously inside a large loop, such as rendering hundreds of grid items, it causes significant main thread blocking and jank. The previous `TEAMCOLOR` function in `index.html` fetched CSS variables dynamically for every single item.

**Action:** Memoize values derived from `getComputedStyle` using a cache map whenever they will be read repeatedly during a render cycle, especially in purely static setups without a modern reactive framework.
## 2026-07-24 - Optimize Rapid Mouseover Events
**Learning:** In a dense grid (300+ items), using `innerHTML` inside a `mouseover` event handler creates a measurable CPU overhead because it triggers synchronous HTML parsing on every rapid interaction. Also, failing to early-return when the same element is hovered causes redundant DOM updates.
**Action:** For high-frequency events like `mouseover`, avoid `innerHTML`. Use `textContent` or modify existing DOM nodes directly. Always check if the target has actually changed before updating the DOM.

## 2026-08-15 - GC Pressure in requestAnimationFrame

**Learning:** Allocating variables and function closures per frame in `requestAnimationFrame` creates severe garbage collection pressure, leading to observable stutters and framerate drops on low-end devices. Passing callbacks to `forEach` on arrays constructed dynamically (`Object.keys`) inside a render loop adds significant latency due to repeated allocations and the JS engine's inability to fully optimize the iterator.

**Action:** Whenever iterating over object properties or arrays inside a hot 60fps render loop (`animate`), pre-allocate the target objects into a module-scoped or cached array. Use classic `for` loops to iterate, and reuse module-scoped vectors (like `THREE.Vector3`) by invoking `.set()` rather than instantiating new objects on every frame.
