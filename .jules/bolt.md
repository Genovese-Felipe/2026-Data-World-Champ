## 2026-07-11 - Costly Synchronous DOM Access in Iteration

**Learning:** `getComputedStyle` is an expensive DOM operation that calculates all styles for an element. When called synchronously inside a large loop, such as rendering hundreds of grid items, it causes significant main thread blocking and jank. The previous `TEAMCOLOR` function in `index.html` fetched CSS variables dynamically for every single item.

**Action:** Memoize values derived from `getComputedStyle` using a cache map whenever they will be read repeatedly during a render cycle, especially in purely static setups without a modern reactive framework.
## 2026-07-23 - Event Debouncing for Heavy Layout Thrashing

**Learning:** Frequent DOM events like `mouseover` or `scroll` that trigger inline style changes, element class toggling, or text replacements on large iteration elements (like a 300-element grid) cause significant layout thrashing. Without throttling, these updates queue up on the main thread, leading to jitter and unresponsiveness. The impact is exacerbated when the user quickly scrubs over many elements and the browser struggles to keep up.

**Action:** Always decouple rapid continuous event listeners from their DOM update payloads. Use `requestAnimationFrame` (and `cancelAnimationFrame` for pending unpainted frames) to ensure updates are batched and only applied once per browser render cycle. Combined with early exits (e.g. checking if the targeted element has already been processed), this guarantees buttery-smooth interaction.
