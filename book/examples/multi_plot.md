# Multi-Plot Examples

This page demonstrates the `multi-plot` directive, which creates grids of mathematical function plots using the `plotmath` library.

## Basic Usage

Three functions in a row:

:::{multiplot}
functions: [x**2, -x, x**3]
rows: 1
cols: 3
:::

## Custom Grid Layout

2x2 grid with four functions:

:::{multiplot}
functions: [x**2, sin(x), exp(x), log(abs(x)+1)]
rows: 2
cols: 2
:::

## With Function Labels

:::{multiplot}
functions: [x**2 - 2*x, -x + 2, x - 3]
fn_labels: [f(x)=x^2-2x, g(x)=-x+2, h(x)=x-3]
rows: 1
cols: 3
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
