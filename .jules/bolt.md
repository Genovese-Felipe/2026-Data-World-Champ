## 2026-07-11 - Costly Synchronous DOM Access in Iteration

**Learning:** `getComputedStyle` is an expensive DOM operation that calculates all styles for an element. When called synchronously inside a large loop, such as rendering hundreds of grid items, it causes significant main thread blocking and jank. The previous `TEAMCOLOR` function in `index.html` fetched CSS variables dynamically for every single item.

**Action:** Memoize values derived from `getComputedStyle` using a cache map whenever they will be read repeatedly during a render cycle, especially in purely static setups without a modern reactive framework.

## 2026-07-22 - Throttling High-Frequency DOM Events with rAF

**Learning:** Rapidly firing DOM events, such as a `mouseover` traversing a highly dense grid, can severely bottleneck the main thread if handlers perform synchronous DOM updates. In this codebase's static layout, moving across 300 tightly packed `div` cells triggered continuous `innerHTML` and `classList` rewrites.

**Action:** Wrap synchronous DOM mutations bound to high-frequency UI events inside `requestAnimationFrame()` (with a debouncing variable to cancel previous frames). Additionally, cache the event target and short-circuit (early return) if the target hasn't changed.
