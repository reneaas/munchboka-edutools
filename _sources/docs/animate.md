# `animate` directive

The `animate` directive creates animated plots by varying one or more variables across frames. It extends the `plot` directive and produces a WebP or GIF file embedded directly in the page.

## Basic usage

To animate a sine wave with varying frequency:

````markdown
:::{animate}
animate-var: a, 1, 5, 20
fps: 10
function: sin(a*x)
xmin: -10
xmax: 10
ymin: -2
ymax: 2
width: 80%
:::
````

which yields:

:::{animate}
animate-var: a, 1, 5, 20
fps: 10
function: sin(a*x)
xmin: -10
xmax: 10
ymin: -2
ymax: 2
width: 80%
:::

## Syntax overview

````markdown
:::{animate}
animate-var: name, start, end, frames
fps: 10
key: value

Optional caption text.
:::
````

The `animate-var` line defines the variable that changes across frames. All `plot` keys (functions, points, lines, polygons, etc.) are available and can reference the animation variable by name.

## Options

| Option | Meaning |
|---|---|
| `animate-var` | Variable spec: `name, start, end, frames` |
| `fps` | Frames per second (default `10`) |
| `duration` | Total duration in seconds (alternative to `fps`) |
| `loop` | Whether to loop (`true`/`false`, default `true`) |
| `format` | Output format: `webp` (default) or `gif` |
| `width` | CSS width |
| `align` | `left`, `center`, or `right` |
| `nocache` | Force regeneration |

All `plot` directive options are also supported (`function`, `point`, `xmin`, `xmax`, `grid`, etc.).

## Examples

### Rotating vector

:::{animate}
animate-var: theta, 0, 360, 36
fps: 12
vector: 0, 0, 3*cos(theta*pi/180), 3*sin(theta*pi/180), blue
point: (0, 0)
xmin: -4
xmax: 4
ymin: -4
ymax: 4
width: 70%
:::

### Moving point on a parabola

:::{animate}
animate-var: t, -3, 3, 30
fps: 15
function: x**2, f
point: (t, f(t))
tangent: t, f, dashed, red
xmin: -4
xmax: 4
ymin: -2
ymax: 10
width: 70%
:::

### Expanding circle

:::{animate}
animate-var: r, 0.5, 3, 20
fps: 8
circle: (0, 0), r, solid, blue
point: (0, 0)
xmin: -4
xmax: 4
ymin: -4
ymax: 4
axis: equal
width: 70%
:::

## Tips

- The directive inherits all drawing primitives from `plot`, so functions, points, tangents, polygons, curves, and macros all work.
- Use `nocache:` during development to force regeneration.
- WebP is the default format and is smaller than GIF.
- Caption text goes after the first blank line in the content.

## Source

The implementation lives in `src/munchboka_edutools/directives/animate.py`.
