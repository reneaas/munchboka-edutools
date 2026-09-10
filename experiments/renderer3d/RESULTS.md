# Renderer comparison results — 10 September 2026

**Recommendation: use Three.js for the next implementation stage.** Its depth
buffer and mesh rendering fit the intended growth toward surfaces and solids.
The existing directive parser, expression trees, geometry helpers, and static
fallback remain useful. This experiment does not switch the production backend.

The evidence favors Three.js for this application, not for every mathematical
interaction. Linked constructions and constrained dragging were outside the
experiment; JSXGraph's facilities remain an advantage for that different focus.

## Visual observations

| Case | JSXGraph adapter | Three.js adapter | Assessment |
|---|---|---|---|
| Line through opaque sphere | The line is drawn continuously over the sphere; native element ordering does not split it at the surface. | The visible portions are solid and the covered portion is faintly dashed. | Three.js provides the more useful foundation for textbook visibility rules. Its dashed hidden pass is custom code, not a default feature. |
| Intersecting translucent planes | Native polygons improve on the previous filled-curve implementation, but their order remains object-based. | Standard transparent-material sorting also orders whole objects; it does not correctly resolve every intersecting overlap. | Neither adapter solves transparency. Do not select Three.js on the assumption that it does. |
| Opaque pyramid | Native polygons produce a readable solid and hide back edges in the tested views. | The solid is readable, with optional dashed hidden edges and lighting cues. | Both are viable for simple solids; Three.js offers more direct control over hidden-edge rendering. |
| Solid of revolution and space curve | The surface is drawable, but the curve's projected path is not reliably depth-resolved against it; updating many SVG faces is expensive here. | Mesh rendering resolves visible/hidden curve portions and combines the surface into one mesh. | Strongest reason to favor Three.js as scenes become denser. |
| Math labels and live coordinates | KaTeX overlays track the geometry. | The same KaTeX overlays track the geometry. | No intrinsic winner: both use the shared label implementation. Long labels can overlap ticks or clip at narrow widths and enlarged layout zoom. |

Inspect the saved comparisons:

- [Sphere and line](results/sphere.png)
- [Transparent planes](results/planes.png)
- [Pyramid](results/pyramid.png)
- [Surface and curve](results/surface.png)
- [Mathematical labels](results/labels.png)
- [Narrow layout](results/mobile.png)
- [Labels at 150% CSS layout zoom](results/label-zoom.png)

Both adapters deliberately keep label overlays visible over solid objects. That
is an authoring policy to revisit, rather than a renderer limitation. The Three.js
hidden pass also includes hidden axis segments, which can clutter a figure; a
production adapter should make that behavior configurable per object category.

## Local update measurements

Median synchronous camera-update times from the final headless Chromium run:

| Case | JSXGraph | Three.js |
|---|---:|---:|
| Sphere and line | 3.0 ms | 0.9 ms |
| Transparent planes | 3.0 ms | 1.0 ms |
| Pyramid | 3.4 ms | 0.9 ms |
| 384-face surface and curve | 24.8 ms | 0.9 ms |
| Labels and construction | 3.2 ms | 1.0 ms |

Method: 24 azimuth positions at 15-degree intervals, fixed 25-degree elevation,
1280 × 1000 browser viewport; discard the first three timing samples and take
the median. Each measurement includes the adapter's camera update and render
call, label positioning, and (for Three.js) copying the shared rendering canvas
to the panel canvas. Unnecessary repeated JSXGraph resize/redraw calls were
removed before taking these results.

These numbers are **not FPS, GPU timer results, or physical-device benchmarks**.
They do not explicitly wait for final browser compositing or all GPU work.
The adapters differ in how geometry is represented: JSXGraph uses individual
polygon elements, while Three.js batches the surface faces into one mesh. The
numbers characterize these proposed implementations, not an exhaustive comparison
of optimized library configurations. First-load compilation, battery cost, memory
under sustained use, and low-end device performance require separate measurement.

[Raw timings and projection checks](results/measurements.json) include initial
geometry-construction times. Those initial construction values also include
label work and are affected by warm caches and adapter initialization order;
they should not be used as a cold-start benchmark.

## Verification

- Eight matched pairs load with all external network requests blocked.
- Projected x/y/z unit points match between renderers to numerical precision
  (maximum discrepancy approximately 1.3e-13 pixels at the initial view).
- A full azimuth sweep completes without JavaScript errors.
- Mouse dragging either renderer changes the synchronized camera.
- The live `a` slider rebuilds the geometry successfully.
- A 390-pixel-wide layout has no horizontal page overflow at normal zoom.
- KaTeX labels render at normal and 150% CSS layout zoom. Screenshots expose
  clipping/overlap at the enlarged narrow layout; this is not a layout pass at
  every zoom level. Real browser UI zoom is distinct from the CSS zoom tested.
- Eight Three.js panels share one WebGL context. Disposing all panels releases
  their GPU geometries; no JavaScript errors remain in the lifecycle check.
- The existing six JavaScript geometry tests still pass.

**Touch-emulation limitation:** the Three.js panel rotated under Chromium's
emulated one-finger gesture; the JSXGraph panel did not in this adapter. This
is recorded in [touch.json](results/touch.json). It is an observed unresolved
adapter/configuration issue, not proof that JSXGraph lacks touch rotation.
Neither adapter has been validated on physical iOS/Android hardware here.

## Implementation findings

The experiment exposed two adapter bugs that were fixed before the final run:

1. JSXGraph's azimuth conversion for a matching z-up view is `90 - azim` for
   this camera setup. Using `90 + azim` mirrors the apparent coordinate-system
   orientation relative to Three.js. The existing production preview still uses
   the older mapping; migration should explicitly define the camera convention.
2. Rebuilding JSXGraph objects must remove them through `view.removeObject`,
   not just `board.removeObject`, to keep the view's depth-order registry current.
   The stale registry caused an SVG hierarchy error after a slider change.

Neither issue should be used as evidence against JSXGraph's rendering model.

## Suggested next stage

Proceed with a Three.js adapter behind the existing scene format, preserving
the current directive interface. Prioritize:

1. Stable point sizes, arrowheads, strokes, and per-object hidden-edge settings.
2. A deliberate transparent-plane policy, with tests at intersecting surfaces.
3. Label collision handling, responsive placement, and real browser/device zoom.
4. Shared-renderer lifecycle, context-loss fallback, and physical-device testing.
5. Full `plot3d-2` geometry and macro parity through the shared mathematical layer.

Keep the static image fallback. Do not expand this experiment into two fully
maintained production backends unless there is a separate need for JSXGraph's
construction system.
