## 2026-07-11 - Costly Synchronous DOM Access in Iteration

**Learning:** `getComputedStyle` is an expensive DOM operation that calculates all styles for an element. When called synchronously inside a large loop, such as rendering hundreds of grid items, it causes significant main thread blocking and jank. The previous `TEAMCOLOR` function in `index.html` fetched CSS variables dynamically for every single item.

**Action:** Memoize values derived from `getComputedStyle` using a cache map whenever they will be read repeatedly during a render cycle, especially in purely static setups without a modern reactive framework.
## 2024-07-23 - Python List Comprehensions inside loops can lead to O(N*C) bottlenecks
**Learning:** In backend data generation, scanning a global list of items (`O(N)`) inside a loop over categories (`O(C)`) results in an `O(N*C)` time complexity, heavily impacting script performance. Grouping lists can resolve this issue.
**Action:** When working with Python data processing tasks involving loops over categories and list comprehensions to filter a global list, perform a single `O(N)` grouping pass first to map items by category. Subsequent lookups become `O(1)`, making the time complexity `O(N)`.
