# `plot3d-2` directive

The `plot3d-2` directive creates 3D mathematical figures in MyST / Jupyter Book using a compact key-value syntax. It uses Matplotlib's 3D axes as the backend, but draws custom centered axes, arrowheads, depth-aware lines, and geometry primitives intended for textbook-style figures.

`plot3d-2` is experimental and is meant to evolve toward feature parity with the mature `plot` directive while keeping the implementation easier to refactor.

## Basic usage

````markdown
:::{plot3d-2}
width: 70%
xrange: (-2, 4)
yrange: (-2, 4)
zrange: (-1, 4)
vector: (0, 0, 0), (2, 1, 3), blue
point: (2, 1, 3), red
text: at=(2, 1, 3), value="$P$", ha=left, va=bottom

Vectoren $\vec{OP}$ i rommet.
:::
````

The directive also has the alias `plot3d2`.

## Syntax overview

The directive is usually written in MyST form:

````markdown
:::{plot3d-2}
key: value
key: value

Optional caption text.
:::
````

You can also use classic reStructuredText syntax:

````markdown
```{eval-rst}
.. plot3d-2::

   width: 70%
   vector: (0, 0, 0), (1, 2, 3), blue

   Optional caption text.
```
````

### How front matter works

- Each non-empty line before the first blank line is interpreted as `key: value` front matter.
- Repeated drawing keys are allowed.
- Lines after the first blank line become the figure caption.
- Most numeric values support arithmetic expressions such as `sqrt(2)`, `pi/3`, and variables created with `let`.

## Supported keys

Repeated drawing keys:

- `angle`
- `curve`
- `line`
- `line-segment`
- `ngon`
- `normal-segment`
- `point`
- `plane`
- `prism`
- `pyramid`
- `right-angle`
- `sphere`
- `solid-of-revolution`
- `text`
- `vector`

Macro keys:

- `let`
- `def`
- `repeat`
- `macro`
- `use`
- `endmacro`

### Quick primitive reference

| Primitive | Minimal syntax |
|---|---|
| `angle` | `angle: dir1=(ax, ay, az), dir2=(bx, by, bz), radius=r, color=color, lw=2` |
| `curve` | `curve: x=f(t), y=g(t), z=h(t), t=(tmin, tmax), color=blue` |
| `line` | `line: point=(x, y, z), direction=(dx, dy, dz), color=blue` |
| `line-segment` | `line-segment: from=(x0, y0, z0), to=(x1, y1, z1), color=blue` |
| `ngon` | `ngon: points=[(x0, y0, z0), (x1, y1, z1), ...], color=blue` |
| `normal-segment` | `normal-segment: point=(px, py, pz), plane=z = x + y, color=blue` |
| `plane` | `plane: equation=z = x + y, color=orange, alpha=0.35` |
| `point` | `point: (x, y, z), color` |
| `prism` | `prism: center=(cx, cy, cz), radius=r, sides=n, height=h, color=blue` |
| `pyramid` | `pyramid: center=(cx, cy, cz), radius=r, sides=n, apex=(x, y, z), color=blue` |
| `right-angle` | `right-angle: at=(x, y, z), dir1=(dx, dy, dz), dir2=(dx, dy, dz), size=0.35` |
| `sphere` | `sphere: center=(x, y, z), radius=r, color=blue` |
| `solid-of-revolution` | `solid-of-revolution: f(x), (xmin, xmax), color` |
| `text` | `text: at=(x, y, z), value="$P$"` |
| `vector` | `vector: (x0, y0, z0), (x1, y1, z1), color` |

## Global options

| Option | Default | Meaning |
|---|---:|---|
| `width` | none | CSS width such as `70%` or `500` |
| `figsize` | `(6, 5)` | Matplotlib figure size in inches |
| `align` | `center` | `left`, `center`, or `right` |
| `class` | none | Extra CSS classes |
| `name` | generated | Stable output name / figure anchor |
| `alt` | `3D-koordinatsystem` | Alt text for accessibility |
| `nocache` | off | Force regeneration |
| `fontsize` | `12` | Base font size for labels and text |
| `lw` | `1.5` | Default line width |
| `xrange` | `(-5, 5)` | Visible x-axis range |
| `yrange` | `(-5, 5)` | Visible y-axis range |
| `zrange` | `(-5, 5)` | Visible z-axis range |
| `xstep` | `1` | x-axis tick spacing |
| `ystep` | `1` | y-axis tick spacing |
| `zstep` | `1` | z-axis tick spacing |
| `xlabel` | `$x$` | x-axis label; use `none` to hide |
| `ylabel` | `$y$` | y-axis label; use `none` to hide |
| `zlabel` | `$z$` | z-axis label; use `none` to hide |
| `axis` | `true` | Turn centered axes, arrowheads, labels, and ticks on or off |
| `grid` | `false` | Draw dashed gray grid lines in the xy-plane at `z=0` |
| `ticks` | `true` | Turn ticks on or off |
| `elev` | `22` | Camera elevation in degrees |
| `azim` | `-55` | Camera azimuth in degrees |
| `zoom` | `1.28` | Camera zoom factor |

Example:

````markdown
:::{plot3d-2}
width: 100%
figsize: (6, 4)
fontsize: 18
lw: 2
axis: off
grid: true
xrange: (-1, 5)
yrange: (-1, 4)
zrange: (-1, 4)
xstep: 1
ystep: 1
zstep: 1
elev: 20
azim: -70
ylabel: none
vector: (0, 0, 0), (3, 2, 2), teal
:::
````

Ticks never include the origin or the two endpoints of an axis. This prevents tick labels from colliding with the origin and the arrowheads.

### Axes and grid

Use `axis: off` to hide the custom centered axes, arrowheads, labels, and ticks. This does not disable primitives.

Use `grid: true` to draw a gray dashed grid in the xy-plane only, at `z = 0`. The grid uses `xrange`, `yrange`, `xstep`, and `ystep`. Unlike tick labels, grid lines include the origin and may include the range endpoints when they land on the step.

````markdown
:::{plot3d-2}
axis: off
grid: true
xrange: (-3, 3)
yrange: (-3, 3)
zrange: (-1, 4)
plane: equation=z = 2, xrange=(-2, 2), yrange=(-2, 2), color=orange, alpha=0.25
point: (1, 1, 2), black
:::
````

## Expression support

Numeric fields support SymPy-style expressions:

- arithmetic: `1/3`, `2*sqrt(5)`, `3*pi/4`
- constants: `pi`, `E`
- functions: `sqrt`, `exp`, `log`, `sin`, `cos`, `tan`, `asin`, `acos`, `atan`, `sinh`, `cosh`, `tanh`, `Abs`
- macro variables and functions created with `let` and `def`

Use `**` for powers.

````markdown
:::{plot3d-2}
point: (sqrt(2), cos(pi/3), 1/2), red
vector: (0, 0, 0), (2*cos(pi/6), 2*sin(pi/6), sqrt(3)), blue
:::
````

## Colors and line styles

Color values may be named plotmath colors such as `blue`, `red`, `green`, `orange`, `purple`, `teal`, `gray`, and `black`, or CSS/Matplotlib color values such as `#13579b`.

Supported line styles for line-like primitives:

- `solid`
- `dashed`
- `dashdot`
- `dotted`

Line-like primitives use depth-aware shading where appropriate. `vector` and `point` primitives are layered above `line` and `line-segment` primitives, so marked endpoints remain visible in construction diagrams.

## Vectors

`vector` draws an arrow from a start point to an end point.

Syntax:

```text
vector: (x0, y0, z0), (x1, y1, z1), color
```

The color is optional and defaults to `blue`.

Options:

| Option | Default | Meaning |
|---|---:|---|
| `color` | `blue` | Vector color, either positional or keyword-style |

Vectors use a custom arrowhead styled to match the 2D `plot` directive.

````markdown
:::{plot3d-2}
xrange: (-1, 4)
yrange: (-1, 4)
zrange: (-1, 4)
vector: (0, 0, 0), (3, 1, 2), blue
vector: (1, 0, 0), (1, 2, 3), orange
:::
````

## Points

`point` draws a marker at a coordinate.

Syntax:

```text
point: (x, y, z), color
```

The color is optional and defaults to `blue`.

````markdown
:::{plot3d-2}
point: (0, 0, 0), black
point: (1, 2, 3), red
text: at=(1, 2, 3), value="$P$", ha=left, va=bottom
:::
````

## Text

`text` places a label at a 3D coordinate.

Syntax:

```text
text: at=(x, y, z), value="label", color=color, fontsize=12, offset=(dx, dy, dz), ha=center, va=center
```

Options:

| Option | Default | Meaning |
|---|---:|---|
| `at` | required | Anchor coordinate |
| `value` or `label` | required | Text content |
| `color` | `black` | Text color |
| `fontsize` | global `fontsize` | Override font size |
| `offset` | `(0, 0, 0)` | Coordinate offset applied to `at` |
| `ha` | `center` | `left`, `center`, or `right` |
| `va` | `center` | `top`, `center`, `bottom`, or `baseline` |

````markdown
:::{plot3d-2}
point: (2, 1, 3), black
text: at=(2, 1, 3), value="$A$", offset=(0.1, 0, 0.1), ha=left, va=bottom
:::
````

## Lines

`line` draws an infinite line clipped to the visible plotting box. Lines use depth shading.

Syntax forms:

```text
line: point=(x0, y0, z0), direction=(dx, dy, dz), color=blue, lw=1.5, style=solid
line: through=[(x0, y0, z0), (x1, y1, z1)], color=blue, lw=1.5, style=solid
line: (x0, y0, z0), (x1, y1, z1), color=blue, lw=1.5, style=solid
```

Options:

| Option | Default | Meaning |
|---|---:|---|
| `color` | `blue` | Line color |
| `lw` | global `lw` | Line width |
| `style` or `linestyle` | `solid` | `solid`, `dashed`, `dashdot`, or `dotted` |

````markdown
:::{plot3d-2}
xrange: (-1, 5)
yrange: (-1, 4)
zrange: (-1, 4)
line: point=(0, 0, 0), direction=(2, 1, 1), color=blue, lw=2
line: through=[(0, 3, 0), (4, 0, 3)], color=red, style=dashed
:::
````

## Line segments

`line-segment` draws only the finite segment between two points. Segments use the same depth-aware rendering as `line`.

Syntax forms:

```text
line-segment: from=(x0, y0, z0), to=(x1, y1, z1), color=blue, lw=1.5, style=solid
line-segment: start=(x0, y0, z0), end=(x1, y1, z1), color=blue, lw=1.5, style=solid
line-segment: (x0, y0, z0), (x1, y1, z1), color, lw=1.5, style=solid
```

Options:

| Option | Default | Meaning |
|---|---:|---|
| `color` | `blue` | Segment color |
| `lw` | global `lw` | Segment width |
| `style` or `linestyle` | `solid` | `solid`, `dashed`, `dashdot`, or `dotted` |

````markdown
:::{plot3d-2}
line-segment: (0, 0, 0), (3, 2, 1), blue, lw=2
line-segment: from=(3, 2, 1), to=(1, 3, 3), color=orange, style=dashed
point: (0, 0, 0), black
point: (3, 2, 1), black
point: (1, 3, 3), black
:::
````

## Normal segments

`normal-segment` draws a perpendicular connector. It has two main forms.

### Normal segment between two lines

Syntax:

```text
normal-segment: point1=(x, y, z), direction1=(dx, dy, dz), point2=(x, y, z), direction2=(dx, dy, dz), color=blue, style=solid
```

Aliases:

- `p1` for `point1`
- `p2` for `point2`
- `dir1` or `v1` for `direction1`
- `dir2` or `v2` for `direction2`

````markdown
:::{plot3d-2}
ticks: off
xrange: (-1, 7)
yrange: (-1, 5)
zrange: (-1, 5)
line: point=(3, 0, 4), direction=(2, 0, 0.5), color=blue, lw=2
line: point=(1, 3, 1), direction=(2, 0, -0.5), color=red, lw=2
normal-segment: point1=(3, 0, 4), direction1=(2, 0, 0.5), point2=(1, 3, 1), direction2=(2, 0, -0.5), color=gray, style=dashed, right-angle-size=0.35
:::
````

By default, the directive draws right-angle markers at both endpoints.

````markdown
:::{plot3d-2}
ticks: off
xrange: (-1, 7)
yrange: (-1, 5)
zrange: (-1, 5)
line: point=(3, 0, 4), direction=(2, 0, 0.5), color=blue, lw=2
line: point=(1, 3, 1), direction=(2, 0, -0.5), color=red, lw=2
normal-segment: p1=(3, 0, 4), v1=(2, 0, 0.5), p2=(1, 3, 1), v2=(2, 0, -0.5), color=gray, style=dashed
:::
````

### Normal segment from a point to a plane

Syntax with plane equation:

```text
normal-segment: point=(px, py, pz), plane=z = x + y, color=blue, style=solid
```

Syntax with normal vector and point on the plane:

```text
normal-segment: point=(px, py, pz), plane-normal=(a, b, c), plane-point=(x0, y0, z0), color=blue, style=solid
```

Aliases:

- `p` for `point`
- `normal` for `plane-normal`
- `plane_point`, `on-plane`, or `on_plane` for `plane-point`
- `equation` for `plane`

Options:

| Option | Default | Meaning |
|---|---:|---|
| `color` | `blue` | Segment color |
| `lw` | global `lw` | Segment width |
| `style` or `linestyle` | `solid` | Segment style |
| `right-angles` | `true` | Draw right-angle marker |
| `right-angle-color` | `black` | Right-angle marker color |
| `right-angle-size` or `size` | `0.35` | Right-angle marker size |
| `points` or `endpoint-points` | `true` | Draw endpoints automatically |
| `endpoint-color` or `point-color` | `black` | Endpoint marker color |

````markdown
:::{plot3d-2}
xrange: (-1, 4)
yrange: (-1, 4)
zrange: (-1, 5)
plane: equation=z = 1, xrange=(-1, 4), yrange=(-1, 4), color=orange, alpha=0.25
normal-segment: point=(2, 2, 4), plane=z = 1, color=gray, style=dashed, right-angle-size=0.35
text: at=(2, 2, 4), value="$P$", ha=left, va=bottom
:::
````

The point-plane form automatically draws a point at the external point and at the foot on the plane. Use `points=off` to suppress those endpoint markers.

For point-plane normal segments, the right-angle marker is drawn with respect to the normal segment and a visible direction in the plane. The marker is chosen to read clearly from the current camera angle.

## Right angles

`right-angle` draws a square right-angle marker at a coordinate.

Syntax with directions:

```text
right-angle: at=(x, y, z), dir1=(dx, dy, dz), dir2=(dx, dy, dz), size=0.35, color=black, lw=1.5
```

Syntax with target points:

```text
right-angle: at=(x, y, z), to1=(x1, y1, z1), to2=(x2, y2, z2), size=0.35, color=black, lw=1.5
```

The `to1` / `to2` form clamps the marker to the distances from `at` to the two target points. This is useful for short segments.

Options:

| Option | Default | Meaning |
|---|---:|---|
| `at` | required | Corner point of the marker |
| `dir1`, `dir2` | required for direction form | Directions that define the right angle |
| `to1`, `to2` | required for target form | Target points that define and clamp the marker |
| `size` | `0.35` | Marker side length |
| `color` | `black` | Marker color |
| `lw` | global `lw` | Marker line width |

````markdown
:::{plot3d-2}
line-segment: (0, 0, 0), (2, 0, 0), black
line-segment: (0, 0, 0), (0, 2, 0), black
right-angle: at=(0, 0, 0), to1=(2, 0, 0), to2=(0, 2, 0), size=0.4, color=red
:::
````

## Angles

`angle` draws a curved angle marker between two 3D directions. The marker is centered at the origin by default, but `at=(x, y, z)` can move it to another point.

```text
angle: dir1=(ax, ay, az), dir2=(bx, by, bz), radius=r, color=color, lw=2
angle: at=(x, y, z), dir1=(ax, ay, az), dir2=(bx, by, bz), radius=r, color=color, lw=2
```

Aliases:

- `direction1` or `v1` for `dir1`
- `direction2` or `v2` for `dir2`
- `r` for `radius`

Options:

| Option | Default | Meaning |
|---|---:|---|
| `at` | `(0, 0, 0)` | Center point of the angle |
| `dir1`, `dir2` | required | Directions spanning the angle |
| `radius` or `r` | `0.35` | Arc radius |
| `color` | `black` | Arc color |
| `lw` | global `lw` | Arc line width |
| `samples` | `64` | Number of sample points along the arc |

The arc is drawn in the plane spanned by `dir1` and `dir2`, using the smaller angle between the directions. Its line color is shaded with respect to the current `elev` / `azim` camera position, so parts closer to the viewer read more strongly. For opposite directions, where no unique plane exists, `plot3d-2` chooses a camera-facing semicircle.

````markdown
:::{plot3d-2}
ticks: off
line-segment: (0, 0, 0), (2, 0, 0), black
line-segment: (0, 0, 0), (0, 2, 1), black
angle: dir1=(1, 0, 0), dir2=(0, 2, 1), radius=0.55, color=purple, lw=2
:::
````

## Planes

`plane` draws a finite patch of a plane.

### Equation form

Syntax:

```text
plane: equation=z = x + y, xrange=(-2, 2), yrange=(-2, 2), color=orange, alpha=0.35
```

The equation may solve for `x`, `y`, or `z`. Use `xrange`, `yrange`, and `zrange` to limit the displayed patch.

````markdown
:::{plot3d-2}
xrange: (-2, 2)
yrange: (-2, 2)
zrange: (-2, 4)
plane: equation=z = x + y, xrange=(-2, 2), yrange=(-2, 2), color=orange, alpha=0.35
:::
````

### Normal-point form

Syntax:

```text
plane: normal=(a, b, c), point=(x0, y0, z0), span=(width, height), color=orange, alpha=0.35
```

`span` controls the finite width and height of the plane patch. If only one value is supplied, the patch is square.

````markdown
:::{plot3d-2}
plane: normal=(1, 1, 1), point=(0, 0, 1), span=(4, 3), color=teal, alpha=0.3
normal-segment: point=(2, 2, 4), plane-normal=(1, 1, 1), plane-point=(0, 0, 1), color=gray, style=dashed
:::
````

## Curves

`curve` draws a parametric 3D curve.

Syntax:

```text
curve: x=f(t), y=g(t), z=h(t), t=(tmin, tmax), color=blue, lw=1.5, samples=300, arrows=true, arrow-count=3
```

Aliases:

- `trange` for `t`
- `arrows-count` for `arrow-count`

Options:

| Option | Default | Meaning |
|---|---:|---|
| `color` | `blue` | Curve color |
| `lw` | global `lw` | Curve width |
| `samples` | `300` | Number of evaluated points, clamped between `2` and `5000` |
| `arrows` | `true` | Draw arrowheads along the curve |
| `arrow-count` | `3` | Number of arrowheads, clamped between `0` and `20` |

Rendering notes:

- Curves use local depth shading.
- Curve style changes by xy-quadrant: solid for `x > 0, y < 0`, dashdot for `x > 0, y > 0` and `x < 0, y > 0`, and dashed for `x < 0, y < 0`.
- Arrowheads lie on the curve and indicate direction.

````markdown
:::{plot3d-2}
xrange: (-2, 2)
yrange: (-2, 2)
zrange: (-1, 14)
curve: x=sin(t), y=cos(t), z=t, t=(0, 4*pi), color=blue, lw=2, samples=400, arrow-count=5
:::
````

Disable arrows with `arrows=false`.

## Solid of revolution

`solid-of-revolution` draws the surface obtained by rotating `f(x)` about the x-axis.

Syntax:

```text
solid-of-revolution: f(x), (xmin, xmax), color
```

The color is optional and defaults to `blue`.

````markdown
:::{plot3d-2}
xrange: (-1, 5)
yrange: (-3, 3)
zrange: (-3, 3)
solid-of-revolution: sqrt(x), (0, 4), green
:::
````

## N-gons

`ngon` draws one filled polygonal face with n corners.

Syntax forms:

```text
ngon: [(x0, y0, z0), (x1, y1, z1), ...], color=blue, edgecolor=black, alpha=0.45
ngon: points=[(x0, y0, z0), (x1, y1, z1), ...], color=blue, edgecolor=black, alpha=0.45
ngon: vertices=[(x0, y0, z0), (x1, y1, z1), ...], color=blue, edgecolor=black, alpha=0.45
```

````markdown
:::{plot3d-2}
ngon: [(0, 0, 0), (2, 0, 0), (2, 1, 1), (0, 1, 1)], color=green, alpha=0.4
:::
````

## Pyramids

`pyramid` draws a pyramid with an n-gon base and an apex.

Syntax with explicit base:

```text
pyramid: base=[(x0, y0, z0), (x1, y1, z1), ...], apex=(x, y, z), color=blue, edgecolor=black, alpha=0.45
pyramid: base=[(x0, y0, z0), (x1, y1, z1), ...], apex=(x, y, z), base-color=blue, side-color=none, edgecolor=black, alpha=0.45
```

Syntax with regular n-gon base in the xy-plane:

```text
pyramid: center=(cx, cy, cz), radius=r, sides=n, apex=(x, y, z), rotation=0, color=blue, edgecolor=black, alpha=0.45
```

`base-color` colors the base face. `side-color` colors the lateral faces. Either can be set to `none` to leave those faces unfilled while preserving edges. `body-color` is accepted as an alias for `side-color`. If `color` is supplied, it overrides both `base-color` and `side-color`.

Options:

| Option | Default | Meaning |
|---|---:|---|
| `base` | required unless using regular base form | Explicit base vertices |
| `center`, `radius`, `sides` | required for regular base form | Regular n-gon base in the xy-plane |
| `rotation` | `0` | Base rotation in radians |
| `apex` | required | Apex coordinate |
| `color` | none | Fill both base and sides; overrides `base-color` and `side-color` |
| `base-color` | `blue` | Base fill color, or `none` |
| `side-color` or `body-color` | `blue` | Lateral face fill color, or `none` |
| `edgecolor` | `black` | Edge color |
| `alpha` | `0.45` | Face opacity |

````markdown
:::{plot3d-2}
xrange: (-2, 2)
yrange: (-2, 2)
zrange: (-1, 3)
pyramid: center=(0, 0, 0), radius=1.4, sides=5, apex=(0, 0, 2.4), base-color=purple, side-color=none, alpha=0.5
:::
````

## Prisms

`prism` draws a prism from an n-gon base and an extrusion.

Syntax with explicit base and vector:

```text
prism: base=[(x0, y0, z0), (x1, y1, z1), ...], vector=(dx, dy, dz), color=blue, edgecolor=black, alpha=0.45
```

Syntax with explicit base and vertical height:

```text
prism: base=[(x0, y0, z0), (x1, y1, z1), ...], height=h, color=blue, edgecolor=black, alpha=0.45
```

Syntax with regular n-gon base:

```text
prism: center=(cx, cy, cz), radius=r, sides=n, height=h, rotation=0, color=blue, edgecolor=black, alpha=0.45
```

````markdown
:::{plot3d-2}
xrange: (-2, 2)
yrange: (-2, 2)
zrange: (-1, 3)
prism: center=(0, 0, 0), radius=1.2, sides=6, height=2, color=yellow, alpha=0.35
:::
````

## Spheres

`sphere` draws a sphere with depth-aware surface shading and guide curves.

Syntax:

```text
sphere: center=(x, y, z), radius=r, color=blue, alpha=0.55, resolution=48
```

`resolution` is clamped between `8` and `128`.

````markdown
:::{plot3d-2}
xrange: (-2, 2)
yrange: (-2, 2)
zrange: (-2, 2)
sphere: center=(0, 0, 0), radius=1, color=skyblue, alpha=0.65, resolution=48
:::
````

## Macros and reusable constructions

`plot3d-2` supports the same macro system style as `plot`.

### `let`

`let` defines a constant expression.

````markdown
:::{plot3d-2}
let: h = 2
point: (1, 0, h), red
vector: (0, 0, 0), (1, 0, h), blue
:::
````

### `def`

`def` defines a helper function. Multi-argument definitions are supported.

````markdown
:::{plot3d-2}
def: px(i, j) = i + j/2
def: pz(i, j) = i*j/3
point: (px(1, 2), 1, pz(1, 2)), red
:::
````

### `repeat`

`repeat` expands one line many times.

````markdown
:::{plot3d-2}
xrange: (-1, 5)
yrange: (-1, 2)
zrange: (-1, 4)
repeat: n=0..4; point: (n, 0, n/2), blue
repeat: n=0..3; line-segment: (n, 0, n/2), (n + 1, 0, (n + 1)/2), gray
:::
````

### `macro` and `use`

Macros package several plot lines into a reusable block.

````markdown
:::{plot3d-2}
macro: pillar(x, y, h, c)
   line-segment: (x, y, 0), (x, y, h), color=c, lw=2
   point: (x, y, h), c
endmacro

use: pillar(0, 0, 1, blue)
use: pillar(1, 1, 2, red)
use: pillar(2, 0, 3, green)
:::
````

## Complete example

````markdown
:::{plot3d-2}
width: 100%
fontsize: 18
elev: 20
azim: -70
grid: true
xrange: (-1, 5)
yrange: (-1, 4)
zrange: (-1, 5)
ylabel: none
plane: equation=z = 1, xrange=(-1, 5), yrange=(-1, 4), color=orange, alpha=0.25
line: point=(0, 0, 1), direction=(1, 0.4, 0), color=blue, lw=2
curve: x=1 + sin(t), y=1 + cos(t), z=1 + t/4, t=(0, 4*pi), color=teal, lw=2, arrow-count=4
normal-segment: point=(3, 2, 4), plane=z = 1, color=gray, style=dashed, right-angle-size=0.35
angle: at=(0, 0, 1), dir1=(1, 0, 0), dir2=(1, 0.4, 0), radius=0.45, color=purple, lw=2
vector: (0, 0, 0), (3, 2, 4), purple
text: at=(3, 2, 4), value="$P$", ha=left, va=bottom

Et punkt, en normal til planet og en romkurve.
:::
````

## Tips

- Use `elev` and `azim` deliberately; the same figure can read very differently from another camera angle.
- Use `ylabel: none` or similar when a label collides with the figure.
- Use `grid: true` when you want a dashed reference grid in the xy-plane without drawing Matplotlib's default 3D panes.
- Use `nocache:` while authoring figures that change often.
- Prefer `line-segment` for finite geometry and `line` for infinite objects clipped to the plotting box.
- Use `normal-segment` for perpendicular constructions instead of manually computing foot points.
- Use `points=off` on point-plane normal segments when automatic endpoint markers create clutter.
- Increase `right-angle-size` when a perpendicular marker is too subtle.
- Use `base-color=none` or `side-color=none` on pyramids when only some faces should be filled.
- Keep `samples` moderate for curves unless the curve really needs high resolution.

## Source

The implementation lives in [src/munchboka_edutools/directives/plot3d_2.py](/Users/reneaas/codes/vgs_books/munchboka-edutools/src/munchboka_edutools/directives/plot3d_2.py).
