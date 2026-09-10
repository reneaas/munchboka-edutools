---
orphan: true
---

# JSXGraph preview migration

The live renderer now uses [Three.js](interactive-plot3d-threejs.md).
Change `backend: jsxgraph` to `backend: threejs`. The earlier name remains a
deprecated alias and emits a build warning.
