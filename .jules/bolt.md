## 2026-07-11 - Costly Synchronous DOM Access in Iteration

**Learning:** `getComputedStyle` is an expensive DOM operation that calculates all styles for an element. When called synchronously inside a large loop, such as rendering hundreds of grid items, it causes significant main thread blocking and jank. The previous `TEAMCOLOR` function in `index.html` fetched CSS variables dynamically for every single item.

**Action:** Memoize values derived from `getComputedStyle` using a cache map whenever they will be read repeatedly during a render cycle, especially in purely static setups without a modern reactive framework.
## 2026-07-24 - Optimize Rapid Mouseover Events
**Learning:** In a dense grid (300+ items), using `innerHTML` inside a `mouseover` event handler creates a measurable CPU overhead because it triggers synchronous HTML parsing on every rapid interaction. Also, failing to early-return when the same element is hovered causes redundant DOM updates.
**Action:** For high-frequency events like `mouseover`, avoid `innerHTML`. Use `textContent` or modify existing DOM nodes directly. Always check if the target has actually changed before updating the DOM.
## 2026-07-29 - Avoid Box-Shadow for Continuous Animations
**Learning:** Animating `box-shadow` on an element with infinite iterations (like a pulse indicator) triggers layout and paint recalculations on the main thread for every frame. This can cause unnecessary continuous CPU overhead and drain battery, especially on complex pages.
**Action:** Use GPU-accelerated properties instead. Create a pseudo-element (`::after` or `::before`) positioned over the target, and animate its `transform: scale()` and `opacity`. This moves the animation entirely to the compositor thread, eliminating repaints.
