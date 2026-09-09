# Live 3D figures with JSXGraph (preview)

Select `backend: jsxgraph` inside `interactive-plot3d` to render an interactive
3D scene in the browser. Sliders are optional: a figure without sliders can still
be rotated and zoomed. The default backend remains `frames` during this preview.

````markdown
:::{interactive-plot3d}
backend: jsxgraph
width: 100%
height: 460px
interactive-var: a, 0, 3, 61
interactive-var-start: 1.5
xrange: (-2, 4)
yrange: (-2, 4)
zrange: (-1, 4)
elev: 22
azim: -55
grid: true
ticks: true
xstep: 1
ystep: 1
zstep: 1
plane: equation=z = 0, color=orange, alpha=0.25
sphere: center=(-1, -1, 1), radius=0.6, color=teal
vector: (0, 0, 0), (a, 1, 2), blue
point: (a, 1, 2), red
line: point=(0, 0, 0), direction=(1, -1, 1), style=dashed
right-angle: at=(0, 0, 0), dir1=(1, 0, 0), dir2=(0, 1, 0), size=0.4
angle: dir1=(1, 0, 0), dir2=(0, 1, 1), radius=0.7
text: at=(a, 1, 2), value="$P$", offset=(0.1, 0.1, 0.1)

Roter koordinatsystemet og flytt punktet med skyveknappen.
:::
````

Drag within the figure to rotate it. The buttons provide keyboard-operable
rotation, tilt, zoom, and reset controls. Moving a geometry slider preserves the
current camera. Sliders used explicitly in `elev`, `azim`, or `zoom` update that
camera setting; reset returns to the camera specified by the current values.

## Implemented in this preview

- Centered axes, arrowheads, labels, and an optional xy grid at `z=0`.
- Axis ranges and tick spacing (`xrange`, `yrange`, `zrange`, `xstep`, `ystep`,
  `zstep`). Each range currently requires a fixed increasing pair. Tick spacing
  must be positive, with at most 200 intervals per axis.
- `axis: off` hides axes, ticks, and axis labels. `ticks: off` hides tick marks
  and their numbers. `xticks`, `yticks`, and `zticks` override tick visibility
  separately. Origin and endpoint ticks are omitted. `xlabel: none` and its
  y/z equivalents hide individual axis labels.
- Points, vectors, infinite lines clipped to the viewing box, and line segments.
- Planes from a linear equation, including vertical planes, or from a normal,
  point, and span. Equation planes are clipped against their specified ranges.
- Spheres, right-angle markers, and angle arcs in their actual 3D planes.
- Text with offsets and slider interpolation, for example `$a = {a:.1f}$`.
- Parametric curves (without arrowheads) and filled `ngon` faces.
- Arithmetic, `pi`, `E`, `sqrt`, `exp`, `log`, trigonometric and hyperbolic
  functions, and `Abs`; powers use `**`. Expressions use a validated arithmetic
  tree, not browser `eval`.
- `let` and `def` declarations, including expressions depending on sliders.
  Declare dependencies before the bindings/functions that use them.
- Captions, anchors, alignment, responsive sizing, and an initial-state PNG
  fallback for JavaScript failure, disabled JavaScript, printing, and LaTeX output.

`interactive-var: a, min, max, frames` retains the existing discrete value count.
The browser evaluates those values live; it does not download pre-rendered frames.
Multiple sliders do not multiply build work. Their initial values use the existing
nearest-step convention, with the middle step selected by default.

JSXGraph 1.13.3 and its MIT license are bundled with the Python package. The
renderer itself requires no CDN or Python in the browser. Math labels use the
page's MathJax when available; otherwise labels display as plain text.

## Remaining parity work

Use `backend: frames` for `normal-segment`, prisms, pyramids, solids of revolution,
`repeat`, `macro`, `use`, and `endmacro`. These produce build errors under the
JSXGraph preview instead of silently disappearing. Draggable points and references
between named objects are not implemented yet.

Curves currently use a single line style, have no direction arrows, and are sampled
at at most 2000 points. Sphere guide circles, camera-facing semicircles for opposite
angle directions, detailed depth shading, hidden-edge styling, and complete
surface occlusion parity remain future work. The static fallback uses `plot3d-2`'s
styling and can differ from the live scene, including per-axis tick overrides.
It always represents the initial slider values, including when printing after
interacting. `usetex` is disabled for this fallback.

The preview hides geometry that becomes undefined at a slider value, and shows a
status message. A right-angle marker disappears when its directions cease to be
perpendicular. Opposite angle directions use a deterministic perpendicular plane.
Ranges, tick spacing, and the global font size must currently be fixed numbers
or constant expressions. Width and height accept positive CSS dimensions;
`height: auto` is not supported in the preview.

Frame-only options (`interactive-workers`, `interactive-max-frames`, `parallel`)
produce migration warnings and are ignored. `nocache` regenerates only the initial
fallback image. `figsize` controls the fallback; use `height` for the live board.

## Development checks

Run the Python/Sphinx regression tests and the JavaScript geometry tests:

```sh
PYTHONPATH=src python -m pytest tests/test_scene3d.py tests/test_plot3d2_directive.py
node --test tests/test_scene3d_runtime.cjs
```

`tests/scene3d_browser.cjs` exercises a Sphinx demo produced by
`tests/test_scene3d.py`'s `build_demo` helper. With Playwright available to Node,
pass the generated HTML directory to the script. Set `MUNCH_CHROMIUM` if using an
existing Chromium installation. The browser check blocks external requests and
verifies geometry, slider updates, camera preservation, mouse rotation, mobile
resizing, multiple figures, printing, and the no-JavaScript fallback.
