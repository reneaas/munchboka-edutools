
# `multiplot` directive

This page demonstrates the `multi-plot` directive, which creates grids of plots of mathematical functions.

## Full Keyword Specification

### Required Options

| Keyword | Type | Description |
|---------|------|-------------|
| `functions` | list | Comma-separated or bracketed list of function expressions (e.g., `[x**2, sin(x), exp(x)]`) |

### Layout & Styling Options

| Keyword | Type | Default | Description |
|---------|------|---------|-------------|
| `rows` | int | auto | Number of rows in the grid |
| `cols` | int | auto | Number of columns in the grid |
| `width` | string | - | Figure width as percentage (e.g., `100%`) or pixels (e.g., `400px`) |
| `align` | string | `center` | Figure alignment: `left`, `center`, or `right` |
| `class` | string | - | Extra CSS classes for the figure container |
| `alt` | string | auto | Accessible description for screen readers |

### Global Axis Options

| Keyword | Type | Default | Description |
|---------|------|---------|-------------|
| `xmin` | float | auto | Global minimum x-axis value |
| `xmax` | float | auto | Global maximum x-axis value |
| `ymin` | float | auto | Global minimum y-axis value |
| `ymax` | float | auto | Global maximum y-axis value |
| `xstep` | float | auto | Spacing between x-axis ticks |
| `ystep` | float | auto | Spacing between y-axis ticks |

### Appearance Options

| Keyword | Type | Default | Description |
|---------|------|---------|-------------|
| `fontsize` | float | 12 | Base font size for labels and ticks |
| `lw` | float | 1.5 | Line width for function curves |
| `alpha` | float | 1.0 | Transparency for function curves (0.0-1.0) |
| `grid` | bool | false | Toggle grid lines (`true`/`false` or `on`/`off`) |
| `ticks` | bool | true | Toggle axis ticks (`true`/`false` or `on`/`off`) |

### Per-Function Options

| Keyword | Aliases | Type | Description |
|---------|---------|------|-------------|
| `fn_labels` | `function-names` | list | LaTeX-formatted labels for each function (e.g., `[f(x)=x^2, g(x)=\sin(x)]`) |
| `domains` | - | list | Domain specifications with optional exclusions (e.g., `[(-5,5) \ {0}, (-2,2)]`) |
| `points` | - | list | Point markers for each plot (e.g., `[[(0,0), (1,1)], None, [(2,4)]]`) |
| `vlines` | - | list | Vertical reference lines per plot (e.g., `[[0, 1], None, [-1]]`) |
| `hlines` | - | list | Horizontal reference lines per plot (e.g., `[[0], None, [1, 2]]`) |
| `lines` | - | list | Linear reference lines y=ax+b per plot (e.g., `[(1, 0), None, (2, -1)]`) |
| `xlims` | - | list | Per-plot x-axis limits (e.g., `[(-3,3), None, (-1,5)]`) |
| `ylims` | - | list | Per-plot y-axis limits (e.g., `[(-5,10), None, (-2,2)]`) |

### Control Options

| Keyword | Type | Default | Description |
|---------|------|---------|-------------|
| `nocache` | bool | false | Force regeneration of the plot (bypass cache) |
| `debug` | bool | false | Keep raw SVG without ID rewriting for inspection |
| `name` | string | auto | Explicit base name for cache filename |

### Usage Notes

- **Functions**: Use SymPy syntax (e.g., `x**2`, `sin(x)`, `exp(x)`, `1/(x-1)`)
- **Domains**: Use set notation for exclusions: `(a,b) \ {x1, x2}` excludes points x1, x2 from interval (a,b)
- **Lists**: Can use brackets `[a, b, c]` or comma-separated `a, b, c`
- **None values**: Use `None` to skip a function in per-function lists (e.g., `vlines: [[0], None, [1]]`)
- **Caption**: Any content after options (or after `---` delimiter) becomes the figure caption
- **Caching**: Plots are cached based on content hash; use `nocache: true` to force regeneration

---

## Basic Usage

### Example 1

Two functions side-by-side on one row:

```markdown
:::{multiplot}
functions: x**2, x**2 * exp(-x)
rows: 1
cols: 2
:::
```

Output:

:::{multiplot}
functions: x**2, x**2 * exp(-x)
rows: 1
cols: 2
:::

### Example 2

A 2x2 grid with four functions:

```markdown
:::{multiplot}
width: 100%
functions: (x - 1) / (x + 1), x / (x**2 - 1), (x**3 - 2*x + 1) / (x - 1), (x**2 - 4) / (x**2 - 1)
function-names: A, B, C, D
rows: 2
cols: 2
ticks: off
:::
```


:::{multiplot}
width: 100%
functions: (x - 1) / (x + 1), x / (x**2 - 1), (x**3 - 2*x + 1) / (x - 1), (x**2 - 4) / (x**2 - 1)
function-names: A, B, C, D
rows: 2
cols: 2
ticks: off
:::




### Example 3


```markdown
:::{multiplot}
functions: x**2 - 2*x, -x + 2
function-names: f(x)=x^2-2x, g(x)=-x+2
rows: 1
cols: 2
width: 100%
:::
```

:::{multiplot}
functions: x**2 - 2*x, -x + 2
function-names: f(x)=x^2-2x, g(x)=-x+2
rows: 1
cols: 2
width: 100%
:::

## Custom Axis Ranges

:::{multiplot}
functions: [tan(x), cos(x)]
xmin: -3.14
xmax: 3.14
ymin: -3
ymax: 3
rows: 1
cols: 2
:::

## With Domain Exclusions

Exclude points where functions are undefined (e.g., division by zero):

:::{multiplot}
functions: [1/x, 1/(x-2), 1/(x**2-1)]
domains: [(-5,5) \ {0}, (-5,5) \ {2}, (-5,5) \ {-1,1}]
rows: 1
cols: 3
:::

## Vertical and Horizontal Reference Lines

:::{multiplot}
functions: [x**2, x**3]
vlines: [[0], [0]]
hlines: [[0], [0]]
rows: 1
cols: 2
:::

## Reference Lines (y = ax + b)

Add a linear reference line to each plot:

:::{multiplot}
functions: [x**2, x**3]
lines: [(1, 0), (1, 0)]
rows: 1
cols: 2
:::

## Per-Axis Limits

Different axis limits for each subplot:

:::{multiplot}
functions: [x**2, sin(x), exp(x)]
xlims: [(-3,3), (-6,6), (-2,2)]
ylims: [(-1,9), (-2,2), (0,8)]
rows: 1
cols: 3
:::

## With Points

Mark specific points on the plots:

:::{multiplot}
functions: [x**2, -x + 1]
points: [[(0,0), (1,1), (-1,1)], [(0,1), (1,0)]]
rows: 1
cols: 2
:::

## Custom Styling

:::{multiplot}
functions: [sin(x), cos(x)]
lw: 3.5
alpha: 0.8
fontsize: 24
grid: true
rows: 1
cols: 2
:::

## YAML-Style Configuration

:::{multiplot}
functions: [x**2, -x**2, x**3, -x**3]
rows: 2
cols: 2
xmin: -3
xmax: 3
ymin: -10
ymax: 10
fontsize: 18
grid: true
width: 80%

Comparison of polynomial functions with different degrees and signs.
:::

## Complex Example

Multiple features combined:

:::{multiplot}
functions: [x**2 - 4, 1/(x-1), sin(2*x)]
fn_labels: [f(x)=x^2-4, g(x)=\frac{1}{x-1}, h(x)=\sin(2x)]
domains: [(-5,5), (-5,5) \ {1}, (-5,5)]
vlines: [[2, -2], None, None]
hlines: [[-4], None, None]
xlims: [(-5,5), (-5,5), (-3.14, 3.14)]
ylims: [(-5,10), (-5,5), (-1.5,1.5)]
rows: 1
cols: 3
width: 100%
fontsize: 20
lw: 2.8

Complex multi-plot demonstrating various features.
:::

## Features

The multi-plot directive supports:
- **Multiple functions** in customizable grid layouts
- **Function labels** using LaTeX notation
- **Domain exclusions** for handling discontinuities
- **Reference lines** (vertical, horizontal, and custom y=ax+b)
- **Point markers** at specific coordinates
- **Per-axis customization** (limits, lines, points)
- **Styling options** (line width, transparency, font size, grid)
- **Responsive sizing** with percentage widths
- **Content-based caching** to avoid regeneration
- **Accessibility** with ARIA labels

## Dependencies

This directive requires the `plotmath` module to be installed.
