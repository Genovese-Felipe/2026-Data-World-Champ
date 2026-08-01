## 2026-07-11 - Costly Synchronous DOM Access in Iteration

**Learning:** `getComputedStyle` is an expensive DOM operation that calculates all styles for an element. When called synchronously inside a large loop, such as rendering hundreds of grid items, it causes significant main thread blocking and jank. The previous `TEAMCOLOR` function in `index.html` fetched CSS variables dynamically for every single item.

**Action:** Memoize values derived from `getComputedStyle` using a cache map whenever they will be read repeatedly during a render cycle, especially in purely static setups without a modern reactive framework.
## 2026-07-24 - Optimize Rapid Mouseover Events
**Learning:** In a dense grid (300+ items), using `innerHTML` inside a `mouseover` event handler creates a measurable CPU overhead because it triggers synchronous HTML parsing on every rapid interaction. Also, failing to early-return when the same element is hovered causes redundant DOM updates.
**Action:** For high-frequency events like `mouseover`, avoid `innerHTML`. Use `textContent` or modify existing DOM nodes directly. Always check if the target has actually changed before updating the DOM.

## 2024-05-30 - GPU-Composited Animations
**Learning:** Found a performance anti-pattern specific to static HTML pages with infinite animations: using `box-shadow` to create a pulsing "live" indicator. Even on an otherwise completely static page, `box-shadow` animations force full CPU repaints on every single frame, draining battery and taking up main thread time unnecessarily.
**Action:** When adding or optimizing infinite or long-running CSS animations, always convert layout/paint-triggering properties (`box-shadow`, `width`, `height`, `top`/`left`) to GPU-composited properties (`transform` and `opacity`) using pseudo-elements if necessary. Additionally, use `will-change: transform` to promote heavily animated containers (like infinite scrolling feeds) to their own compositing layer.
