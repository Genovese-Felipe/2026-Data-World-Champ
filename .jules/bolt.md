## 2026-07-11 - Costly Synchronous DOM Access in Iteration

**Learning:** `getComputedStyle` is an expensive DOM operation that calculates all styles for an element. When called synchronously inside a large loop, such as rendering hundreds of grid items, it causes significant main thread blocking and jank. The previous `TEAMCOLOR` function in `index.html` fetched CSS variables dynamically for every single item.

**Action:** Memoize values derived from `getComputedStyle` using a cache map whenever they will be read repeatedly during a render cycle, especially in purely static setups without a modern reactive framework.
## 2026-07-24 - Optimize Rapid Mouseover Events
**Learning:** In a dense grid (300+ items), using `innerHTML` inside a `mouseover` event handler creates a measurable CPU overhead because it triggers synchronous HTML parsing on every rapid interaction. Also, failing to early-return when the same element is hovered causes redundant DOM updates.
**Action:** For high-frequency events like `mouseover`, avoid `innerHTML`. Use `textContent` or modify existing DOM nodes directly. Always check if the target has actually changed before updating the DOM.
## 2026-08-02 - JSON Serialization Padding

**Learning:** When using build scripts like Python's `json.dump` to generate static data payloads, default settings (or explicit indentation like `indent=1`) include unnecessary whitespace that significantly increases output file size. Over 10-15% of the payload can be wasted purely on structural whitespace.
**Action:** Always utilize minification arguments like `separators=(',', ':')` in data generation scripts for static sites lacking a conventional bundler/minifier, reducing unnecessary network overhead on the client.
