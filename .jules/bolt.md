## 2024-07-09 - CSS Variable Computation in Render Loops
**Learning:** `getComputedStyle` is an expensive DOM operation that causes synchronous layout/style recalculations. In `index.html`, `TEAMCOLOR` queries `getComputedStyle(document.documentElement)` repeatedly inside loops over hundreds of predictions/data points.
**Action:** Implement a memoized version of `TEAMCOLOR` using a closure or simple object cache to avoid repeated expensive DOM lookups for CSS variables.
