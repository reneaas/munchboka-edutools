# `plot` directive

The `plot` directive creates mathematical figures directly in MyST / Jupyter Book using a compact key-value syntax. It is designed for textbook-style figures and supports functions, points, labels, polygons, vectors, parametric curves, and a macro system for building repeated structures.

## Basic usage

To plot a function, we can write the following:

````markdown
:::{plot}
width: 70%
function: (x - 1)**2 - 4, f
:::
````

which yields the following output:

:::{plot}
width: 70%
function: (x - 1)**2 - 4, f
:::

## Syntax overview

The directive is usually written in MyST form:

````markdown
:::{plot}
key: value
key: value

Optional caption text.
:::
````

You can also use classic reStructuredText syntax:

````markdown
```{eval-rst}
.. plot::

	 width: 70%
	 function: sin(x), f

	 Optional caption text.
```
````

### How front matter works

- Each non-empty line before the first blank line is interpreted as `key: value` front matter.
- Repeated keys are allowed for drawing several objects of the same type.
- Lines after the first blank line become the figure caption.

## Supported keys

The directive supports repeated drawing keys:

- `function`
- `point`
- `annotate`
- `text`
- `vline`
- `hline`
- `line`
- `tangent`
- `polygon`
- `fill-polygon`
- `fill-between`
- `bar`
- `vector`
- `line-segment`
- `angle-arc`
- `circle`
- `ellipse`
- `curve`
- `axis`

It also supports scalar options such as figure size, axis limits, labels, fonts, caching, and macro definitions.

## Global options

| Option | Meaning |
|---|---|
| `width` | CSS width such as `70%` or `500` |
| `figsize` | Matplotlib figure size, e.g. `(6, 4)` |
| `align` | `left`, `center`, or `right` |
| `class` | Extra CSS classes |
| `name` | Stable output name / figure anchor |
| `alt` | Alt text for accessibility |
| `nocache` | Force regeneration |
| `debug` | Keep extra debug output |
| `usetex` | Force LaTeX text rendering on or off |
| `handdrawn` | Use Matplotlib's XKCD-style rendering |
| `fontsize` | Base font size |
| `lw` | Default line width |
| `alpha` | Default line alpha |
| `xmin`, `xmax`, `ymin`, `ymax` | Axis limits |
| `xstep`, `ystep` | Tick spacing |
| `ticks` | Turn ticks on or off |
| `xticks`, `yticks` | Turn one axis' ticks off with `off` |
| `grid` | Turn grid on or off |
| `xlabel`, `ylabel` | Axis labels, optionally with padding |
| `function-endpoints` | Draw endpoint markers for functions |
| `endpoint_markers` | Legacy alias for `function-endpoints` |

## Expression support

Most numeric fields support SymPy expressions. This includes:

- arithmetic like `1/3`, `2*sqrt(5)`, `3*pi/4`
- constants such as `pi` and `E`
- functions such as `sqrt`, `exp`, `log`, `sin`, `cos`, `tan`, `asin`, `acos`, `atan`

For example:

````markdown
:::{plot}
function: sin(x)
point: (pi/2, 1)
circle: (0, 0), sqrt(2)
line-segment: (0, 0), (2*cos(pi/6), 2*sin(pi/6))
:::
````

## Functions

### Basic function syntax

You can plot a function with or without a label:

````markdown
:::{plot}
function: x**2 - 1
function: -x + 2, g
width: 70%
:::
````

which yields:

:::{plot}
function: x**2 - 1
function: -x + 2, g
width: 70%
:::

### Domains and exclusions

Domains can be open, closed, or mixed, and you can exclude points inside the interval.

````markdown
:::{plot}
function: 1 / x, f, (-4, 4) \ {0}
xmin: -5
xmax: 5
ymin: -5
ymax: 5
:::
````

which yields:

:::{plot}
function: 1 / x, f, (-4, 4) \ {0}
xmin: -5
xmax: 5
ymin: -5
ymax: 5
:::

### Endpoint markers

Endpoint markers can be enabled with `function-endpoints: true`.

````markdown
:::{plot}
function-endpoints: true
function: sqrt(x), f, [0, 4]
function: -sqrt(x), g, (0, 4]
xmin: -1
xmax: 5
ymin: -3
ymax: 3
:::
````

### Tangents

Tangents can be drawn to labeled functions. The simplest form is:

````markdown
:::{plot}
function: -x**2 + 4, f
tangent: 1, f, solid, red
point: (1, f(1))
:::
````

## Points, labels, and annotations

### Points

Points can be given directly, and their coordinates may use function labels such as `f(2)`.

````markdown
:::{plot}
function: x**2 - 1, f
point: (2, f(2))
point: (-1, 0)
:::
````

### Text labels

Text labels support positions such as `top-left`, `bottom-center`, and `center-center`. You can also add a bounding box.

````markdown
:::{plot}
function: (x - 1)**2 - 2
text: 1, -2, "Toppunkt", top-center, bbox
width: 70%
:::
````

which yields:

:::{plot}
function: (x - 1)**2 - 2
text: 1, -2, "Toppunkt", top-center, bbox
width: 70%
:::

### Annotations

Annotations draw an arrow from a text position to a target point.

````markdown
:::{plot}
function: sin(x)/x, f, (-10, 10) \ {0}
annotate: (4, 2), (pi, f(pi)), "Interessant punkt", 0.2
xmin: -10
xmax: 10
ymin: -1
ymax: 3
:::
````

## Vertical lines, horizontal lines, and straight lines

### Vertical and horizontal lines

````markdown
:::{plot}
function: (x - 1) / (x + 2), f
vline: -2, dashed, red
hline: 1, dotted, blue
xmin: -6
xmax: 6
ymin: -6
ymax: 6
:::
````

### General lines

The `line` key supports several forms:

- `line: a, b` for `y = ax + b`
- `line: a, (x0, y0)` for a line with slope `a` through `(x0, y0)`
- `line: (x1, y1), (x2, y2)` for a line through two points

````markdown
:::{plot}
line: 1, -1, dashed, red
line: -1/2, (2, 1), dotted, blue
line: (-2, -1), (3, 2), solid, green
xmin: -4
xmax: 4
ymin: -4
ymax: 4
:::
````

### Line segments

`line-segment` draws only the finite segment between two points.

````markdown
:::{plot}
line-segment: (0, 0), (3, 2), solid, blue
line-segment: (3, 2), (4, 0), dashed, orange
point: (0, 0)
point: (3, 2)
point: (4, 0)
xmin: -1
xmax: 5
ymin: -1
ymax: 3
:::
````

which yields:

:::{plot}
line-segment: (0, 0), (3, 2), solid, blue
line-segment: (3, 2), (4, 0), dashed, orange
point: (0, 0)
point: (3, 2)
point: (4, 0)
xmin: -1
xmax: 5
ymin: -1
ymax: 3
:::

## Polygons and filled regions

### Polygons

`polygon` draws a polygon outline and can optionally fill it if a color is provided.

````markdown
:::{plot}
polygon: (0, 0), (2, 0), (1, 1.5), show_vertices, purple, 0.2
xmin: -1
xmax: 3
ymin: -1
ymax: 2
:::
````

### Filled polygons

`fill-polygon` fills the polygon interior.

````markdown
:::{plot}
fill-polygon: (0, 0), (2, 0), (1, 1.5), orange, 0.3
polygon: (0, 0), (2, 0), (1, 1.5), black
xmin: -1
xmax: 3
ymin: -1
ymax: 2
:::
````

### Fill between curves

`fill-between` fills the region between two function expressions.

````markdown
:::{plot}
function: x**2 / 4, f
function: x + 2, g
fill-between: x + 2, x**2 / 4, (-2, 4), blue, 0.2, where=above
xmin: -3
xmax: 5
ymin: -1
ymax: 7
:::
````

which yields:

:::{plot}
function: x**2 / 4, f
function: x + 2, g
fill-between: x + 2, x**2 / 4, (-2, 4), blue, 0.2, where=above
xmin: -3
xmax: 5
ymin: -1
ymax: 7
:::

## Bars, vectors, angle arcs, circles, ellipses, and curves

### Bars

````markdown
:::{plot}
bar: (0, 0), 3, horizontal
bar: (4, 0), 2, vertical
xmin: -1
xmax: 6
ymin: -1
ymax: 3
:::
````

### Vectors

`vector` supports start-plus-components or start-and-end-point forms.

````markdown
:::{plot}
vector: 0, 0, 2, 1, teal
vector: (0, 0), (1, 2), orange
xmin: -1
xmax: 3
ymin: -1
ymax: 3
:::
````

### Angle arcs

````markdown
:::{plot}
line-segment: (0, 0), (3, 0), solid, black
line-segment: (0, 0), (2, 2), solid, black
angle-arc: (0, 0), 1.2, 0, 45, dashed, red
xmin: -1
xmax: 4
ymin: -1
ymax: 3
:::
````

### Circles, ellipses, and parametric curves

````markdown
:::{plot}
circle: (0, 0), 1, fill, blue
ellipse: (3, 0), 1.5, 0.8, dashed, purple
curve: 5 + cos(t), sin(2*t), (0, 2*pi), solid, green
xmin: -2
xmax: 7
ymin: -2
ymax: 2
axis: equal
:::
````

which yields:

:::{plot}
circle: (0, 0), 1, fill, blue
ellipse: (3, 0), 1.5, 0.8, dashed, purple
curve: 5 + cos(t), sin(2*t), (0, 2*pi), solid, green
xmin: -2
xmax: 7
ymin: -2
ymax: 2
axis: equal
:::

## Axes, labels, and layout

### Axis control

Use `axis: off` to hide the coordinate system and `axis: equal` to force equal scaling.

````markdown
:::{plot}
circle: (0, 0), 1, solid, blue
axis: off
axis: equal
xmin: -2
xmax: 2
ymin: -2
ymax: 2
:::
````

### Ticks and grid

````markdown
:::{plot}
function: sin(x)
xmin: -2*pi
xmax: 2*pi
ymin: -2
ymax: 2
xstep: pi/2
grid: true
ticks: true
:::
````

### Axis labels

You can provide a label alone or a label together with padding.

````markdown
:::{plot}
function: x**2
xlabel: $x$, 8
ylabel: $y$, 8
width: 70%
:::
````

## Macros and reusable constructions

The macro system is useful when a figure contains repeated structure.

### `let`

`let` defines a constant expression.

````markdown
:::{plot}
let: a = 2
let: b = 3
point: (a, b)
:::
````

### `def`

`def` defines a helper function. Multi-argument definitions are supported.

````markdown
:::{plot}
def: px(i, j) = i + j/2
def: py(i, j) = j / 3
point: (px(1, 2), py(1, 2))
xmin: -1
xmax: 3
ymin: -1
ymax: 2
:::
````

### `repeat`

`repeat` expands one line many times, and repeats can be nested.

````markdown
:::{plot}
def: px(i, j) = i + j/3
def: py(i, j) = j / 4
repeat: i=0..1; repeat: j=0..2; point: (px(i, j), py(i, j))
xmin: -1
xmax: 3
ymin: -1
ymax: 2
:::
````

### `macro` and `use`

Macros let you package several plot lines into one reusable block.

````markdown
:::{plot}
macro: shortseg(x0, y0, color)
	line-segment: (x0, y0), (x0 + 1, y0), solid, color
	point: (x0, y0)
endmacro

use: shortseg(0, 0, blue)
use: shortseg(0, 1, red)

xmin: -1
xmax: 2
ymin: -1
ymax: 2
:::
````

which yields:

:::{plot}
macro: shortseg(x0, y0, color)
	line-segment: (x0, y0), (x0 + 1, y0), solid, color
	point: (x0, y0)
endmacro

use: shortseg(0, 0, blue)
use: shortseg(0, 1, red)

xmin: -1
xmax: 2
ymin: -1
ymax: 2
:::

### Local scope inside macros

`let` and `def` written inside a macro body are local to that macro invocation. They do not leak into the outer scope and do not collide across separate `use:` calls.

````markdown
:::{plot}
let: d = 0

macro: scopedseg(i, color)
	let: d = i / 10
	def: px(x) = x + d
	line-segment: (px(0), i / 5), (px(1/5), i / 5), solid, color
endmacro

use: scopedseg(1, #aa0000)
use: scopedseg(2, #00aa00)
line-segment: (d, 0), (d + 0.08, 0), solid, black

xmin: -0.1
xmax: 0.5
ymin: -0.1
ymax: 0.6
axis: off
:::
````

## Complete example

The following example combines several features in one figure.

````markdown
:::{plot}
width: 100%
fontsize: 22
function: sin(x)/x, f, (-6*pi, 6*pi) \ {0}
point: (pi, f(pi))
text: pi, f(pi), "$P$", top-right, bbox
annotate: (5, 1.5), (pi, f(pi)), "Merket punkt", 0.15
vline: 0, dotted, gray
hline: 0, dotted, gray
circle: (0, 0), 1, dashed, teal
curve: 3 + cos(t), sin(2*t), (0, 2*pi), solid, orange
xlabel: $x$
ylabel: $y$
xmin: -8
xmax: 8
ymin: -2
ymax: 3
:::
````

which yields:

:::{plot}
width: 100%
fontsize: 22
function: sin(x)/x, f, (-6*pi, 6*pi) \ {0}
point: (pi, f(pi))
text: pi, f(pi), "$P$", top-right, bbox
annotate: (5, 1.5), (pi, f(pi)), "Merket punkt", 0.15
vline: 0, dotted, gray
hline: 0, dotted, gray
circle: (0, 0), 1, dashed, teal
curve: 3 + cos(t), sin(2*t), (0, 2*pi), solid, orange
xlabel: $x$
ylabel: $y$
xmin: -8
xmax: 8
ymin: -2
ymax: 3
:::

## Tips

- Prefer labels on important functions if you want to reference them later with `f(2)` or use tangents.
- Use `axis: equal` for circles, ellipses, geometric constructions, and fractal-like figures.
- Use `nocache:` while authoring a figure that changes often.
- Use `function-endpoints: true` when the exact endpoint behavior matters pedagogically.
- Use macros when a figure is structurally repetitive.

## Source

The implementation lives in [src/munchboka_edutools/directives/plot.py](/Users/reneaas/codes/vgs_books/munchboka-edutools/src/munchboka_edutools/directives/plot.py).


