# Bounded 3D renderer comparison

This is an isolated experiment, not a new directive backend. The production
`interactive-plot3d` configuration is unchanged.

## Run the comparison

From the repository root:

```sh
PYTHONPATH=src python experiments/renderer3d/build_cases.py
python -m http.server 8766 --bind 127.0.0.1
```

Open http://127.0.0.1:8766/experiments/renderer3d/ . The checked-in `cases.json`
can be used without running Python. Serve the page over HTTP: the JavaScript
modules cannot reliably load directly from a `file:` URL.

The page contains five substantive cases and three additional simple pairs:

1. A line through an opaque sphere.
2. Intersecting translucent planes.
3. An opaque pyramid and its edges.
4. A 384-face solid of revolution and a parametric curve.
5. Live coordinates, angle markers, and mathematical labels.
6. Three additional independent figures to exercise the shared renderer.

Drag either member of a pair to synchronize its camera with the other. Use the
sliders for repeatable camera positions and the `a` slider for live geometry.

## Controls on the comparison

- The existing scene parser and arithmetic/geometry runtime generate the inputs.
  `mesh` is an experiment-only fixture containing explicit faces and edges; it
  does not extend the directive's public syntax.
- Both renderers use identical world coordinates, z-up orthographic cameras,
  base colors, HTML label overlays, KaTeX, and camera controls.
- JSXGraph uses native `polygon3d` faces, rather than the production preview's
  filled `curve3d` workaround. This tests a more capable JSXGraph implementation.
- Three.js triangulates and combines the surface faces into a single mesh. It
  uses `Line2` for controllable stroke widths and two depth-tested line passes:
  solid visible portions and faint dashed hidden portions.
- JSXGraph uses its native depth ordering. The matching dashed-hidden-line
  algorithm is **not implemented** in its adapter. The comparison demonstrates
  the behavior and effort of these implementations, not that JSXGraph could
  never implement such a feature.
- Three.js uses modest lighting; JSXGraph's faces use flat fills. Lighting is an
  explicit visual difference. Labels are always overlaid, even behind solids.
- There is one shared WebGL renderer/context. Each Three.js panel receives an
  immediate copy of its rendered image into a local 2D canvas. Rendering occurs
  on changes, without a perpetual animation loop. This avoids one WebGL context
  per figure, but adds a canvas-copy cost and requires production validation.

## Findings and evidence

See [RESULTS.md](RESULTS.md) for observations, timing methodology, screenshots,
the touch-emulation outcome, and a recommendation. Raw measurements are stored
under `results/`.

With Playwright available to Node, run:

```sh
node experiments/renderer3d/check.cjs
```

Set `NODE_PATH` if Playwright is installed outside this repository, and
`MUNCH_CHROMIUM` to use an existing Chromium executable. The server must already
be running on port 8766. The check rejects non-local network requests, tests
camera matching, mouse rotation, sliders, layout, labels, and resource cleanup,
and records touch emulation separately. Temporary captures go to `/tmp`.

## Vendored dependencies

The experiment uses the production copy of JSXGraph 1.13.3 and these isolated
dependencies, which are not added to the Python package's production assets:

- Three.js 0.180.0: selected modules from
  https://registry.npmjs.org/three/-/three-0.180.0.tgz . MIT license in
  `vendor/three/LICENSE`.
- KaTeX 0.16.22: JavaScript, CSS, and WOFF2 fonts from
  https://registry.npmjs.org/katex/-/katex-0.16.22.tgz . MIT license in
  `vendor/katex/LICENSE`.

All required assets are local. This pins a stable comparison, rather than
depending on whichever release a CDN supplies later.
