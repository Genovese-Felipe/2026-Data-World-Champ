## 2026-07-11 - Costly Synchronous DOM Access in Iteration

**Learning:** `getComputedStyle` is an expensive DOM operation that calculates all styles for an element. When called synchronously inside a large loop, such as rendering hundreds of grid items, it causes significant main thread blocking and jank. The previous `TEAMCOLOR` function in `index.html` fetched CSS variables dynamically for every single item.

**Action:** Memoize values derived from `getComputedStyle` using a cache map whenever they will be read repeatedly during a render cycle, especially in purely static setups without a modern reactive framework.

## 2026-07-12 - Expensive Box-Shadow Animations

**Learning:** Animating `box-shadow` (e.g. for a pulsing dot indicator) triggers continuous paint and layout operations, which is extremely expensive for the main thread and can cause jank on lower-end devices.

**Action:** Whenever a pulsing or glowing effect is needed, implement it by animating `transform: scale()` and `opacity` on a `::before` or `::after` pseudo-element. These properties are GPU-accelerated and do not trigger layout/paint operations, freeing up the main thread.
