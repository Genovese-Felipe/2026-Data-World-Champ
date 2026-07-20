## 2026-07-11 - Costly Synchronous DOM Access in Iteration

**Learning:** `getComputedStyle` is an expensive DOM operation that calculates all styles for an element. When called synchronously inside a large loop, such as rendering hundreds of grid items, it causes significant main thread blocking and jank. The previous `TEAMCOLOR` function in `index.html` fetched CSS variables dynamically for every single item.

**Action:** Memoize values derived from `getComputedStyle` using a cache map whenever they will be read repeatedly during a render cycle, especially in purely static setups without a modern reactive framework.

## 2026-10-24 - O(N*M) Iteration Cost in Python Data Processing

**Learning:** When aggregating data by a categorical feature (like `camp` in `PREDICTIONS`), doing a list comprehension filtering the entire dataset for each category inside a loop results in O(N * M) time complexity (where N is dataset size, M is categories). While `Counter` is efficient, constantly recreating the filtered list is not.

**Action:** Whenever iterating through a collection to filter by distinct categories, group the items into a `defaultdict(list)` first in an O(N) pass, then process the grouped data.
