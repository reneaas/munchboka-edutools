# `interactive-graph` directive

The `interactive-graph` directive creates an interactive plot with a slider that lets users explore mathematical functions by changing a variable value in real-time. It pre-renders all frames during the build and uses an efficient delta format for fast client-side display.

## Basic usage

An interactive graph of Riemann sums (left-endpoint rectangles) where the slider controls the number of rectangles:

````markdown
:::{interactive-graph}
interactive-var: N, 1, 64, 64
interactive-var-start: 1
function: 1/9 * (x + 1) * (x - 6) ** 2, f, blue
xmin: -2
xmax: 9
ymin: -2
ymax: 7
let: a = 0
let: b = 6
let: h = (b - a) / N
repeat: n=0..N-1; polygon: (a + n * h, 0), (a + (n + 1) * h, 0), (a + (n + 1) * h, f(a + n * h)), (a + n * h, f(a + n * h)), blue, 0.3
:::
````

:::{interactive-graph}
interactive-var: N, 1, 64, 64
interactive-var-start: 1
function: 1/9 * (x + 1) * (x - 6) ** 2, f, blue
xmin: -2
xmax: 9
ymin: -2
ymax: 7
let: a = 0
let: b = 6
let: h = (b - a) / N
repeat: n=0..N-1; polygon: (a + n * h, 0), (a + (n + 1) * h, 0), (a + (n + 1) * h, f(a + n * h)), (a + n * h, f(a + n * h)), blue, 0.3
:::

## Syntax overview

The directive uses the same key-value content format as the `plot` directive, with additional interactive-specific keys:

````markdown
:::{interactive-graph}
interactive-var: name, min, max, frames
interactive-var-start: value

function: expr, label, color
point: (x, y), color, size
text: x, y, "text with {name:.2f}", anchor
xmin: -10
xmax: 10
ymin: -5
ymax: 5
:::
````

### Interactive variable

The `interactive-var` key defines the slider variable:

```
interactive-var: name, min, max, frames
```

- **name** — variable name used in expressions (e.g. `N`, `a`, `t`)
- **min** — minimum slider value
- **max** — maximum slider value
- **frames** — number of pre-rendered frames

Use `interactive-var-start` to set the initial slider position (defaults to the first frame).

### Variable substitution

The interactive variable can be used in any expression — functions, points, text labels, `let` definitions, and `repeat` loops. Text labels support format specifiers like `{N:.2f}` or `{N:0.f}`.

## Options

The directive inherits all options from the `plot` directive, plus:

| Option | Meaning | Default |
|---|---|---|
| `interactive-var` | Slider variable: `name, min, max, frames` | *(required)* |
| `interactive-var-start` | Initial slider value | first frame |
| `interactive-max-frames` | Safety limit for multi-variable frame count | `10000` |
| `interactive-workers` | Number of parallel worker processes | auto |
| `parallel` | Enable parallel frame rendering: `true`/`false` | `false` |
| `width` | CSS width | — |
| `height` | CSS height | — |
| `align` | `left`, `center`, or `right` | — |
| `nocache` | Force regeneration of all frames | — |

All `plot` drawing keys are supported: `function`, `point`, `line`, `tangent`, `polygon`, `fill-polygon`, `fill-between`, `text`, `annotate`, `vline`, `hline`, `vector`, `circle`, `curve`, `let`, `def`, `repeat`, `macro`, `use`, etc.

## Examples

### Right-endpoint Riemann sums

````markdown
:::{interactive-graph}
parallel: true
interactive-var: N, 1, 64, 64
interactive-var-start: 1
function: 1/9 * (x + 1) * (x - 6) ** 2, f, blue
xmin: -2
xmax: 9
ymin: -2
ymax: 7
let: a = 0
let: b = 6
let: h = (b - a) / N
repeat: n=0..N-1; polygon: (a + n * h, 0), (a + (n + 1) * h, 0), (a + (n + 1) * h, f(a + n * h)), (a + n * h, f(a + n * h)), blue, 0.3
nocache:
:::

:::{interactive-graph} 
parallel: true
interactive-var: N, 1, 64, 64
interactive-var-start: 1
function: 1/9 * (x + 1) * (x - 6) ** 2, f, blue
xmin: -2
xmax: 9
ymin: -2
ymax: 7
let: a = 0
let: b = 6
let: h = (b - a) / N
repeat: n=0..N-1; polygon: (a + n * h, 0), (a + (n + 1) * h, 0), (a + (n + 1) * h, f(a + (n + 1) * h)), (a + n * h, f(a + n * h)), blue, 0.3
nocache:
:::


:::{interactive-graph} 
width: 100%
fontsize: 24
interactive-var: N, 1, 64, 64
interactive-var-start: 5
xmin: -1
xmax: 6
ymin: -1
ymax: 11
function: 10 * 3**-x, (0, 5), f, blue
let: a = 0
let: b = 5
let: h = (b - a) / N
let: M = N - 1
repeat: n=0..M; polygon: (a + n * h, 0), (a + (n + 1) * h, 0), (a + (n + 1) * h, f(a + n * h)), (a + n * h, f(a + n * h)), blue, 0.3
text: 6, 5, "{N:0.f} rektangler", bbox
:::