## 2026-07-11 - Costly Synchronous DOM Access in Iteration

**Learning:** `getComputedStyle` is an expensive DOM operation that calculates all styles for an element. When called synchronously inside a large loop, such as rendering hundreds of grid items, it causes significant main thread blocking and jank. The previous `TEAMCOLOR` function in `index.html` fetched CSS variables dynamically for every single item.

**Action:** Memoize values derived from `getComputedStyle` using a cache map whenever they will be read repeatedly during a render cycle, especially in purely static setups without a modern reactive framework.
## 2026-07-24 - Optimize Rapid Mouseover Events
**Learning:** In a dense grid (300+ items), using `innerHTML` inside a `mouseover` event handler creates a measurable CPU overhead because it triggers synchronous HTML parsing on every rapid interaction. Also, failing to early-return when the same element is hovered causes redundant DOM updates.
**Action:** For high-frequency events like `mouseover`, avoid `innerHTML`. Use `textContent` or modify existing DOM nodes directly. Always check if the target has actually changed before updating the DOM.
## 2026-08-05 - Memoizing Repeated String Manipulation

**Learning:** Pure functions performing string manipulation and math (like `hexA` converting hex to RGBA strings) inside tight rendering loops (e.g., generating a heat matrix for 110+ items) can consume noticeable CPU time, especially on less powerful devices. When the domain of inputs is small (like a few team colors and alpha levels), these recalculations are highly redundant.

**Action:** For pure helper functions called repeatedly with the same arguments during UI generation, attach a static cache object to the function itself (e.g., `func.cache = func.cache || {}`) and memoize the results using a unique key derived from the arguments.
