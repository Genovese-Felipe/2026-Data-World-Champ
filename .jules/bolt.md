## 2026-07-11 - Costly Synchronous DOM Access in Iteration

**Learning:** `getComputedStyle` is an expensive DOM operation that calculates all styles for an element. When called synchronously inside a large loop, such as rendering hundreds of grid items, it causes significant main thread blocking and jank. The previous `TEAMCOLOR` function in `index.html` fetched CSS variables dynamically for every single item.

**Action:** Memoize values derived from `getComputedStyle` using a cache map whenever they will be read repeatedly during a render cycle, especially in purely static setups without a modern reactive framework.
## 2026-07-24 - Optimize Rapid Mouseover Events
**Learning:** In a dense grid (300+ items), using `innerHTML` inside a `mouseover` event handler creates a measurable CPU overhead because it triggers synchronous HTML parsing on every rapid interaction. Also, failing to early-return when the same element is hovered causes redundant DOM updates.
**Action:** For high-frequency events like `mouseover`, avoid `innerHTML`. Use `textContent` or modify existing DOM nodes directly. Always check if the target has actually changed before updating the DOM.

## 2026-10-29 - Costly GC in Render Loops
**Learning:** In a high-frequency loop like `requestAnimationFrame`, generating arrays dynamically (e.g. `Object.keys().forEach()`, `.map()`) or continuously allocating objects (e.g., `new THREE.Vector3()`) adds significant pressure to the garbage collector (GC), potentially causing jank.
**Action:** Lift array computations to initialization code, keeping an array of relevant items instead of reading objects dynamically inside render functions. Also, reuse pre-allocated objects like `THREE.Vector3` instead of spawning new instances per frame.
