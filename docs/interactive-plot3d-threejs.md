# Interactive 3D figures with Three.js

Use `backend: threejs` inside `interactive-plot3d` for live 3D math graphs.
Sliders are optional; all figures support rotation and zoom. The existing
`frames` backend remains the default during migration. The earlier `jsxgraph`
backend name is a deprecated alias for `threejs` and emits a build warning.

## Live example gallery

Each figure below is followed by the complete Markdown used to create it.
Drag a figure to rotate it, and use its sliders or view buttons to explore.

### 1. Vectors, points, and custom ticks

Move `a` to change the vector and point. This example combines a coordinate grid, custom tick spacing, a line, a plane, a sphere, and angle markers.

:::{interactive-plot3d}
backend: threejs
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

**Markdown source**

````markdown
:::{interactive-plot3d}
backend: threejs
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

### 2. A perpendicular from a point to a plane

Move `h` to change the height of the point. The foot and right-angle marker are constructed automatically; the plane stays fixed.

:::{interactive-plot3d}
backend: threejs
width: 100%
height: 440px
interactive-var: h, 1, 4, 31
interactive-var-start: 3
xrange: (-2, 4)
yrange: (-2, 4)
zrange: (-1, 5)
ticks: off
plane: equation=z=0, color=orange, alpha=0.25
point: (1,1,h), red
normal-segment: point=(1,1,h), plane=z=0, color=blue, right-angle-size=0.4
text: at=(1,1,h), offset=(0.3,0.3,0.2), value="$P=(1,1,{h:.1f})$", fontsize=15
text: at=(1,1,0), offset=(0.3,0.3,-0.2), value="$H$", fontsize=15

The segment PH is perpendicular to the plane z=0.
:::

**Markdown source**

````markdown
:::{interactive-plot3d}
backend: threejs
width: 100%
height: 440px
interactive-var: h, 1, 4, 31
interactive-var-start: 3
xrange: (-2, 4)
yrange: (-2, 4)
zrange: (-1, 5)
ticks: off
plane: equation=z=0, color=orange, alpha=0.25
point: (1,1,h), red
normal-segment: point=(1,1,h), plane=z=0, color=blue, right-angle-size=0.4
text: at=(1,1,h), offset=(0.3,0.3,0.2), value="$P=(1,1,{h:.1f})$", fontsize=15
text: at=(1,1,0), offset=(0.3,0.3,-0.2), value="$H$", fontsize=15

The segment PH is perpendicular to the plane z=0.
:::
````

### 3. An angle that changes with a vector

Move `a` to change the angle in the xy-plane. The square marker is deliberately shown only when the two directions are perpendicular (`a=0`).

:::{interactive-plot3d}
backend: threejs
width: 100%
height: 440px
interactive-var: a, -2, 2, 41
interactive-var-start: 0
xrange: (-3, 4)
yrange: (-2, 4)
zrange: (-2, 3)
ticks: off
elev: 50
azim: -65
vector: (0,0,0), (3,0,0), blue
vector: (0,0,0), (a,3,0), red
angle: at=(0,0,0), dir1=(1,0,0), dir2=(a,3,0), radius=1, color=teal
right-angle: at=(0,0,0), dir1=(1,0,0), dir2=(a,3,0), size=0.35
text: at=(3,0,0), offset=(0,0,0.3), value="$u$", fontsize=16
text: at=(a,3,0), offset=(0,0,0.3), value="$v=({a:.1f},3,0)$", fontsize=16

The arc follows the angle between u and v.
:::

**Markdown source**

````markdown
:::{interactive-plot3d}
backend: threejs
width: 100%
height: 440px
interactive-var: a, -2, 2, 41
interactive-var-start: 0
xrange: (-3, 4)
yrange: (-2, 4)
zrange: (-2, 3)
ticks: off
elev: 50
azim: -65
vector: (0,0,0), (3,0,0), blue
vector: (0,0,0), (a,3,0), red
angle: at=(0,0,0), dir1=(1,0,0), dir2=(a,3,0), radius=1, color=teal
right-angle: at=(0,0,0), dir1=(1,0,0), dir2=(a,3,0), size=0.35
text: at=(3,0,0), offset=(0,0,0.3), value="$u$", fontsize=16
text: at=(a,3,0), offset=(0,0,0.3), value="$v=({a:.1f},3,0)$", fontsize=16

The arc follows the angle between u and v.
:::
````

### 4. A prism and a pyramid with shared height

Move `h` to change both solids. Axes and ticks are hidden to focus on the shapes. Dashed hidden edges are visible through the opaque prism.

:::{interactive-plot3d}
backend: threejs
width: 100%
height: 440px
interactive-var: h, 0.5, 3, 26
interactive-var-start: 2
xrange: (-3, 4)
yrange: (-3, 3)
zrange: (-1, 4)
axis: off
hidden-edges: dashed
prism: center=(-1.5,0,0), radius=1, sides=5, height=h, color=teal, alpha=1
pyramid: base=[(0.5,-1,0),(2.5,-1,0),(2.5,1,0),(0.5,1,0)], apex=(1.5,0,h), color=blue, alpha=0.55
text: at=(-1.5,0,h), offset=(0,0,0.4), value="Prism", fontsize=16
text: at=(1.5,0,h), offset=(0,0,0.4), value="Pyramid", fontsize=16

Two solids controlled by the same height parameter.
:::

**Markdown source**

````markdown
:::{interactive-plot3d}
backend: threejs
width: 100%
height: 440px
interactive-var: h, 0.5, 3, 26
interactive-var-start: 2
xrange: (-3, 4)
yrange: (-3, 3)
zrange: (-1, 4)
axis: off
hidden-edges: dashed
prism: center=(-1.5,0,0), radius=1, sides=5, height=h, color=teal, alpha=1
pyramid: base=[(0.5,-1,0),(2.5,-1,0),(2.5,1,0),(0.5,1,0)], apex=(1.5,0,h), color=blue, alpha=0.55
text: at=(-1.5,0,h), offset=(0,0,0.4), value="Prism", fontsize=16
text: at=(1.5,0,h), offset=(0,0,0.4), value="Pyramid", fontsize=16

Two solids controlled by the same height parameter.
:::
````

### 5. A helix on a cylinder

Move `r` to change the radius of both the curve and the surface. The curve runs around the x axis, matching the convention for solids of revolution.

:::{interactive-plot3d}
backend: threejs
width: 100%
height: 440px
interactive-var: r, 0.4, 1.4, 21
interactive-var-start: 0.8
xrange: (-1, 5)
yrange: (-2, 2)
zrange: (-2, 2)
ticks: off
elev: 25
azim: -65
solid-of-revolution: r, (0,4), teal, samples=24, radial-samples=40, alpha=0.2
curve: x=t/pi, y=r*cos(t), z=r*sin(t), t=(0,4*pi), samples=400, color=red, lw=2.5, arrows=true, arrow-count=4
point: (4,r,0), red
text: at=(2,0,1.7), value="$r={r:.1f}$", fontsize=16

A parametric helix and a surface of revolution share a live radius.
:::

**Markdown source**

````markdown
:::{interactive-plot3d}
backend: threejs
width: 100%
height: 440px
interactive-var: r, 0.4, 1.4, 21
interactive-var-start: 0.8
xrange: (-1, 5)
yrange: (-2, 2)
zrange: (-2, 2)
ticks: off
elev: 25
azim: -65
solid-of-revolution: r, (0,4), teal, samples=24, radial-samples=40, alpha=0.2
curve: x=t/pi, y=r*cos(t), z=r*sin(t), t=(0,4*pi), samples=400, color=red, lw=2.5, arrows=true, arrow-count=4
point: (4,r,0), red
text: at=(2,0,1.7), value="$r={r:.1f}$", fontsize=16

A parametric helix and a surface of revolution share a live radius.
:::
````

### 6. Reusable constructions with macros and repeats

Move `a` to change the heights of three pillars. A macro defines one pillar and its label; `use` places three copies, and `repeat` places the reference points.

:::{interactive-plot3d}
backend: threejs
width: 100%
height: 440px
interactive-var: a, 0.5, 2, 16
interactive-var-start: 1
xrange: (-1, 5)
yrange: (-2, 2)
zrange: (-1, 5)
ticks: off
let: height = a**2
macro: pillar(pos, h)
prism: center=(pos,0,0), radius=0.4, sides=4, height=h, color=teal, alpha=0.8
text: at=(pos,0,h), offset=(0,0,0.3), value="Pillar pos", fontsize=14
endmacro
use: pillar(1, height)
use: pillar(2, 2*height/3)
use: pillar(3, height/3)
repeat: i=1..3; point: (i,-1,0), red

Reusable geometry and repeated points update without pre-rendered frames.
:::

**Markdown source**

````markdown
:::{interactive-plot3d}
backend: threejs
width: 100%
height: 440px
interactive-var: a, 0.5, 2, 16
interactive-var-start: 1
xrange: (-1, 5)
yrange: (-2, 2)
zrange: (-1, 5)
ticks: off
let: height = a**2
macro: pillar(pos, h)
prism: center=(pos,0,0), radius=0.4, sides=4, height=h, color=teal, alpha=0.8
text: at=(pos,0,h), offset=(0,0,0.3), value="Pillar pos", fontsize=14
endmacro
use: pillar(1, height)
use: pillar(2, 2*height/3)
use: pillar(3, height/3)
repeat: i=1..3; point: (i,-1,0), red

Reusable geometry and repeated points update without pre-rendered frames.
:::
````

markdown
:::{interactive-plot3d}
backend: threejs
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

Drag to rotate, scroll or pinch to zoom, or use the keyboard-accessible view
buttons. Geometry sliders preserve the camera. A slider used in `elev`, `azim`,
or `zoom` updates that setting. Reset uses the camera expressions at the current
slider values. Coordinates are right-handed with z pointing up. Camera angles
are in degrees; regular polygon `rotation` and trigonometric expressions use radians.

## Supported authoring features

- Axes with arrowheads, labels, fixed ranges and custom tick spacing; an optional
  xy grid at z=0. Use `axis: off`, `ticks: off`, or individual `xticks`, `yticks`,
  `zticks`. `xlabel: none` (and y/z equivalents) hides an axis label.
- Points, vectors, line segments, infinite lines clipped to the viewing box,
  planes from linear equations or normal/point/span, and spheres.
- Angle arcs in their 3D plane, right-angle markers, and normal segments between
  a point and a plane or between two lines.
- Filled polygons, prisms, pyramids, parametric curves with direction arrows,
  and surfaces of revolution about the x axis.
- `let`, `def`, `repeat`, and reusable `macro`/`use` blocks. Expressions remain
  live when sliders change. Declare binding dependencies before using them.
- Text with offsets, alignment, mixed prose and `$math$`, and slider interpolation
  such as `$a = {a:.1f}$`. Bundled KaTeX renders labels without a CDN.
- Captions, anchors, alignment, responsive dimensions, and initial-state PNG
  fallbacks for printing, LaTeX, disabled JavaScript, or unavailable WebGL.

`interactive-var: a, min, max, frames` keeps the existing discrete value count.
Values are evaluated in the browser; multiple sliders do not multiply build work.
Initial values use the nearest step, defaulting to the middle step.

Additional geometry examples (put these in a directive's settings block):

```text
normal-segment: point=(1,1,a), plane=z=0, color=red
normal-segment: point1=(0,0,0), direction1=(1,0,0), point2=(0,2,3), direction2=(0,1,0)
prism: center=(0,0,0), radius=1, sides=5, height=a, color=teal
pyramid: base=[(0,0,0),(2,0,0),(0,2,0)], apex=(0,0,a), side-color=blue
solid-of-revolution: sqrt(x+a), (0,2), blue, samples=40, radial-samples=32
curve: x=cos(t), y=sin(t), z=t/4, t=(0,2*pi), arrows=true, arrow-count=3
repeat: i=1..3; point: (i,0,a), red
macro: pillar(h)
prism: center=(0,0,0), radius=0.4, sides=4, height=h
endmacro
use: pillar(a)
```

Prisms accept `vector=(dx,dy,dz)` instead of `height`. Regular bases require
`center`, `radius`, and `sides`; explicit bases use `base=[(...), ...]`.
Pyramids accept `base-color=none` or `side-color=none` to omit those faces.
Normal segments support `right-angles=false` and `points=false` to hide markers.
Use `hidden-edges: dashed` globally or `hidden-edges=dashed` on a primitive
for a dashed pass behind opaque surfaces. It is off by default.

## Rendering and migration limits

Three.js 0.180.0 and KaTeX 0.16.22 are bundled with MIT licenses. ES modules
use relative imports and need a page served over HTTP(S); opening HTML directly
with `file://` may show only the static fallback. Figures share one WebGL context
and render on demand. Unchanged geometry is retained when a slider moves;
removing figures releases their controls and graphics resources.

This is a functional live backend, with visual parity work still outstanding:
intersecting transparent surfaces can sort imperfectly; sphere guide circles,
legacy depth shading, and camera-facing opposite-angle semicircles are not yet
matched. Labels stay within the board, but crowded labels may overlap. Points
are drawn as screen-sized markers and are not draggable. Object references and
constraints between named points are not yet supported. Mobile gestures have
Chromium emulation coverage; physical-device verification remains to be done.

The fallback uses `plot3d-2` styling and always shows initial slider values,
including when printing after interaction. Per-axis tick overrides and optional
hidden-edge styling can differ from the live scene. `usetex` is disabled for the
fallback. Undefined objects are omitted with a status message; right-angle
markers disappear if their directions cease to be perpendicular.

Axis ranges, tick spacing, and global font size must be constant. Each axis is
limited to 200 tick intervals. Curves have at most 2000 samples; regular bases
have 3–200 sides; repeats have integer inclusive bounds and the expanded scene
is limited to 1000 primitives. Surface sampling is limited to 160 by 96.
Arithmetic supports `pi`, `E`, `sqrt`, `exp`, `log`, trigonometric/hyperbolic
functions, and `Abs`, with `**` for powers. A validated arithmetic tree is used
instead of JavaScript `eval`; the broader legacy SymPy language is not supported.

Frame-only options (`interactive-workers`, `interactive-max-frames`, `parallel`)
warn and are ignored. `nocache` refreshes the initial fallback. `figsize` controls
the fallback; use positive CSS `height`/`width` dimensions for the live board.
`height: auto` is not supported. Use `backend: frames` when an existing figure
needs a legacy feature not yet supported here.

## Remaining implementation plan

1. Validate representative textbook figures and physical touch devices; refine
   label placement, transparent surfaces, and sphere/angle styling.
2. Audit remaining `plot3d-2` options and shared static/live scene semantics.
3. Switch the default from `frames` once that compatibility audit passes, with
   migration notes and explicit `backend: frames` retained for older figures.
4. Add draggable points and dependent constructions as a separate extension.

## Development checks

```sh
PYTHONPATH=src python -m pytest tests/test_scene3d.py tests/test_plot3d2_directive.py
node --test tests/test_scene3d_runtime.cjs
```

`tests/scene3d_browser.cjs /path/to/demo/html` starts a local server and checks
bundled assets, sliders, camera preservation, mouse/touch rotation, math labels,
responsive sizing, multiple figures, context recovery, disposal, printing, and
no-JavaScript/no-WebGL fallbacks. Generate its fixture using `build_demo` in
`tests/test_scene3d.py`; Playwright is required, and `MUNCH_CHROMIUM` can select
an existing Chromium executable.
