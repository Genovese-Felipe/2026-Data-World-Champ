## 2026-07-11 - Costly Synchronous DOM Access in Iteration

**Learning:** `getComputedStyle` is an expensive DOM operation that calculates all styles for an element. When called synchronously inside a large loop, such as rendering hundreds of grid items, it causes significant main thread blocking and jank. The previous `TEAMCOLOR` function in `index.html` fetched CSS variables dynamically for every single item.

**Action:** Memoize values derived from `getComputedStyle` using a cache map whenever they will be read repeatedly during a render cycle, especially in purely static setups without a modern reactive framework.

## 2026-07-11 - Hidden O(N^2) in List Comprehensions
**Learning:** Using a list comprehension to filter a large array (`[p for p in PREDICTIONS if p["camp"] == c]`) inside a loop effectively creates an O(N * M) nested loop. When the list is large and the loop runs multiple times, this becomes a significant CPU bottleneck.
**Action:** When filtering a dataset multiple times by a categorical key, always pre-group the data into a hash map (`defaultdict(list)`) in a single O(N) pass, then use O(1) dictionary lookups inside the subsequent loops.
