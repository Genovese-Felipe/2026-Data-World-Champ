## 2026-07-07 - Memoize getComputedStyle calls
**Learning:** Repeatedly calling `getComputedStyle(document.documentElement).getPropertyValue(...)` inside tight loops (like DOM rendering or grid generation) causes significant synchronous main-thread blocking, because the browser must repeatedly resolve style calculations.
**Action:** Always memoize or cache the results of CSS custom property lookups when they are static and accessed repeatedly within JavaScript rendering loops.
