## 2026-07-11 - Costly Synchronous DOM Access in Iteration

**Learning:** `getComputedStyle` is an expensive DOM operation that calculates all styles for an element. When called synchronously inside a large loop, such as rendering hundreds of grid items, it causes significant main thread blocking and jank. The previous `TEAMCOLOR` function in `index.html` fetched CSS variables dynamically for every single item.

**Action:** Memoize values derived from `getComputedStyle` using a cache map whenever they will be read repeatedly during a render cycle, especially in purely static setups without a modern reactive framework.

## 2026-07-14 - Continuous CSS Animations (Layout/Paint vs Compositor)
**Learning:** Continuous CSS animations using properties like `box-shadow` trigger expensive layout and paint operations continuously on the main thread. This can cause jank, high CPU usage, and drain battery, especially on elements that are always visible like a "live" indicator.
**Action:** Always offload continuous visual animations to the compositor thread by using `transform` (e.g., `scale()`) and `opacity` on a pseudo-element instead of animating layout/paint properties directly on the main element.
