## 2023-10-25 - [DOM Performance]
**Learning:** Calling `getComputedStyle` multiple times inside a loop (like iterating through hundreds of items to get their specific color CSS variable) causes significant style recalculation overhead and performance bottlenecks.
**Action:** Memoize the results of `getComputedStyle` to ensure each CSS variable is only computed once, bringing the lookup from O(N) style queries down to O(1) cache hits.
