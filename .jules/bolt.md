## 2026-07-11 - Costly Synchronous DOM Access in Iteration

**Learning:** `getComputedStyle` is an expensive DOM operation that calculates all styles for an element. When called synchronously inside a large loop, such as rendering hundreds of grid items, it causes significant main thread blocking and jank. The previous `TEAMCOLOR` function in `index.html` fetched CSS variables dynamically for every single item.

**Action:** Memoize values derived from `getComputedStyle` using a cache map whenever they will be read repeatedly during a render cycle, especially in purely static setups without a modern reactive framework.
## 2026-07-12 - High-Frequency Event Thrashing

**Learning:** When attaching a `mouseover` event listener to a container with many children (like a grid of 300 cells), the event can fire rapidly as the mouse moves within the same cell or across cell boundaries. Processing every event, especially those that write to the DOM via `innerHTML`, causes unnecessary layout thrashing, layout recalculations, and HTML parsing.

**Action:** Implement an early return in high-frequency event handlers to ignore events that target the already-active element. Furthermore, avoid using `innerHTML` for dynamic content updates inside such listeners; instead, pre-construct the necessary DOM structure and update `textContent` and inline styles, avoiding expensive HTML parsing during interaction.
