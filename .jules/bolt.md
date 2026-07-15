## 2026-07-11 - Costly Synchronous DOM Access in Iteration

**Learning:** `getComputedStyle` is an expensive DOM operation that calculates all styles for an element. When called synchronously inside a large loop, such as rendering hundreds of grid items, it causes significant main thread blocking and jank. The previous `TEAMCOLOR` function in `index.html` fetched CSS variables dynamically for every single item.

**Action:** Memoize values derived from `getComputedStyle` using a cache map whenever they will be read repeatedly during a render cycle, especially in purely static setups without a modern reactive framework.
## 2026-07-12 - Box-Shadow Animations Are Inefficient

**Learning:** CSS animations on properties like `box-shadow` trigger expensive repaint and layout operations on every frame, which can cause significant jank, especially on mobile devices or lower-end machines.

**Action:** Replace layout-triggering animated properties like `box-shadow` with composite properties like `transform` and `opacity` on a pseudo-element. This allows the browser to offload the animation to the GPU.
