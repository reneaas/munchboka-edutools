# Multi-Plot Point Keyword Examples

This page demonstrates the new `point` keyword for the `multi-plot` directive.

## Example 1: Using function evaluation with flattened index

:::{multi-plot}
functions: (x - 1)**2 + 1, 2*(x - 1), -x + 2, (x - 1) / (x + 2)
function-names: f, g, h, p
rows: 2
cols: 2
point: (1, f(2)), 1
:::

In this example, `point: (1, f(2)), 1` adds the point (1, f(2)) to axis 1 (first plot, top-left). The value `f(2)` is evaluated using the function f(x) = (x-1)² + 1.

## Example 2: Using (row, col) format with function evaluation

:::{multi-plot}
functions: (x - 1)**2 + 1, 2*(x - 1), -x + 2, (x - 1) / (x + 2)
function-names: f, g, h, p
rows: 2
cols: 2
point: (1, h(2)), (2, 1)
:::

In this example, `point: (1, h(2)), (2, 1)` adds the point (1, h(2)) to the axis at row 2, column 1 (third plot, bottom-left, function h).

## Example 3: Multiple points with function evaluation

:::{multi-plot}
functions: (x - 1)**2 + 1, 2*(x - 1), -x + 2, (x - 1) / (x + 2)
function-names: f, g, h, p
rows: 2
cols: 2
point: (2, f(2)), 1
point: (0, g(0)), 2
point: (-1, h(-1)), (2, 1)
point: (2, p(2)), (2, 2)
:::

This example shows multiple `point` entries targeting different axes, each evaluating their respective functions.

## Example 4: Combining with legacy points keyword

:::{multi-plot}
functions: x**2, -x, x**3, sin(x)
function-names: f, g, h, p
rows: 2
cols: 2
points: [(0, 0), None, None, None]
point: (1, g(1)), 2
point: (-1, h(-1)), 3
:::

You can mix the legacy `points` keyword (per-axis lists) with the new `point` keyword (axis-targeted).

## Example 5: Numeric coordinates (no function calls)

:::{multi-plot}
functions: x**2, -x + 1, x - 2, 2*x
rows: 2
cols: 2
point: (1, 1), 1
point: (0, 1), 2
point: (2, 0), (2, 1)
point: (-1, -2), 4
:::

The `point` keyword also works with plain numeric coordinates.

## HLine Examples

### Example 6: Basic horizontal line

:::{multi-plot}
functions: x**2, -x, x**3, sin(x)
rows: 2
cols: 2
hline: 2, 1
hline: -1, 3
:::

Full-width horizontal lines at y=2 on axis 1 and y=-1 on axis 3.

### Example 7: Horizontal line with x-extent

:::{multi-plot}
functions: x**2, -x + 2, x**3, sin(x)
function-names: f, g, h, p
rows: 2
cols: 2
hline: 1, -2, 2, 1
hline: g(1), 0, 3, (1, 2)
:::

Horizontal lines with specified x-ranges: from x=-2 to x=2 at y=1 on axis 1, and from x=0 to x=3 at y=g(1) on row 1, col 2.

### Example 8: Combining point and hline

:::{multi-plot}
functions: (x - 1)**2 + 1, 2*(x - 1), -x + 2, (x - 1) / (x + 2)
function-names: f, g, h, p
rows: 2
cols: 2
point: (1, f(1)), 1
point: (2, g(2)), 2
hline: 2, 1
hline: 3, -1, 1, (2, 1)
:::

You can combine `point` and `hline` keywords to mark both points and reference lines on specific axes.

## VLine Examples

### Example 9: Basic vertical line

:::{multi-plot}
functions: x**2, -x, x**3, sin(x)
rows: 2
cols: 2
vline: 1, 1
vline: -2, 3
:::

Full-height vertical lines at x=1 on axis 1 and x=-2 on axis 3.

### Example 10: Vertical line with y-extent

:::{multi-plot}
functions: x**2, -x + 2, x**3, sin(x)
function-names: f, g, h, p
rows: 2
cols: 2
vline: 1, -2, 2, 1
vline: sqrt(2), 0, 3, (1, 2)
:::

Vertical lines with specified y-ranges: from y=-2 to y=2 at x=1 on axis 1, and from y=0 to y=3 at x=sqrt(2) on row 1, col 2.

### Example 11: Combining point, hline, and vline

:::{multi-plot}
functions: (x - 1)**2 + 1, 2*(x - 1), -x + 2, (x - 1) / (x + 2)
function-names: f, g, h, p
rows: 2
cols: 2
point: (1, f(1)), 1
point: (2, g(2)), 2
hline: 2, 1
vline: 1, -2, 2, 1
hline: 3, -1, 1, (2, 1)
vline: 0, (2, 1)
:::

You can combine `point`, `hline`, and `vline` keywords to create comprehensive reference markers on specific axes.

## Using the `line` keyword

The `line` keyword allows you to add reference lines with axis targeting. It supports two forms:
- Slope-intercept: `line: a, b, axis_spec` for y = a*x + b
- Point-slope: `line: a, (x0, y0), axis_spec` for a line with slope a through point (x0, y0)

### Example 12: Basic line with slope-intercept form

:::{multi-plot}
functions: x**2, -x + 2, x**3, sin(x)
function-names: f, g, h, p
rows: 2
cols: 2
line: 2, 1, 1
line: -1, 2, 3
:::

Adds y = 2x + 1 on axis 1 and y = -x + 2 on axis 3.

### Example 13: Line with point-slope form

:::{multi-plot}
functions: x**2, -x + 2, x**3, sin(x)
function-names: f, g, h, p
rows: 2
cols: 2
line: 2, (1, 3), 1
line: -1, (0, 2), (2, 1)
:::

Adds line with slope 2 through (1, 3) on axis 1, and slope -1 through (0, 2) on row 2, col 1.

### Example 14: Line with function evaluation

:::{multi-plot}
functions: x**2 - 2*x + 1, -x + 2, x**3, sin(x)
function-names: f, g, h, p
rows: 2
cols: 2
point: (1, f(1)), 1
point: (4, f(4)), 1
line: (f(4) - f(1)) / 3, (1, f(1)), 1
:::

Adds secant line through (1, f(1)) and (4, f(4)) using computed slope on axis 1.

### Example 15: Combining all reference markers

:::{multi-plot}
functions: (x - 1)**2 + 1, 2*(x - 1), -x + 2, (x - 1) / (x + 2)
function-names: f, g, h, p
rows: 2
cols: 2
point: (1, f(1)), 1
point: (2, g(2)), 2
hline: 2, 1
vline: 1, -2, 2, 1
line: 2, -1, 3
line: 1, (0, 2), (2, 1)
:::

You can combine `point`, `hline`, `vline`, and `line` keywords for comprehensive visualization.

## Using the `tangent` keyword

The `tangent` keyword allows you to add tangent lines to functions at specified points. The derivative is computed automatically using SymPy.

### Example 16: Basic tangent line

:::{multi-plot}
functions: (x - 1)**2 + 1, -2*(x + 2)**3, x**2 * exp(-x), -2*x + exp(x)
function-names: f, g, h, p
rows: 2
cols: 2
tangent: 2, f, 1
tangent: -1, g, 2
:::

Adds tangent to f at x=2 on axis 1, and tangent to g at x=-1 on axis 2.

### Example 17: Tangent with (row, col) addressing

:::{multi-plot}
functions: x**3 - 3*x, sin(x), exp(-x**2), log(x + 2)
function-names: f, g, h, p
rows: 2
cols: 2
tangent: 1, f, (1, 1)
tangent: pi/2, g, (1, 2)
tangent: 0, h, (2, 1)
:::

Tangent lines on row 1 col 1 (f at x=1), row 1 col 2 (g at x=π/2), and row 2 col 1 (h at x=0).

### Example 18: Tangent with point marker

:::{multi-plot}
functions: x**2, sin(x), exp(x), log(x)
function-names: f, g, h, p
rows: 2
cols: 2
point: (2, f(2)), 1
tangent: 2, f, 1
point: (1, g(1)), 2
tangent: 1, g, 2
:::

Combines tangent lines with point markers at the points of tangency.

### Example 19: Multiple tangents on same axis

:::{multi-plot}
functions: x**3 - 4*x, -x + 2, x**2, sin(x)
function-names: f, g, h, p
rows: 2
cols: 2
tangent: -1, f, 1
tangent: 1, f, 1
point: (-1, f(-1)), 1
point: (1, f(1)), 1
:::

Multiple tangent lines can be added to the same axis. This example shows two tangents to f(x) = x³ - 4x at x=-1 and x=1.

## Using per-axis limits

The `xmin`, `xmax`, `ymin`, and `ymax` keywords allow you to set axis limits either globally or per-axis.

### Example 20: Per-axis limits with axis targeting

:::{multi-plot}
functions: x**2, sin(x), exp(x), log(x + 1)
function-names: f, g, h, p
rows: 2
cols: 2
xmin: -5, 1
xmax: 5, 1
ymin: 0, 1
xmin: -2*pi, 2
xmax: 2*pi, 2
:::

Sets custom x and y limits for axis 1 (x from -5 to 5, y from 0 to default), and custom x limits for axis 2 (x from -2π to 2π).

### Example 21: Global limits applied to all axes

:::{multi-plot}
functions: x**2, x**3, 2*x, -x + 1
rows: 2
cols: 2
xmin: -3
xmax: 3
ymin: -5
ymax: 5
:::

Sets the same limits for all axes: x from -3 to 3, y from -5 to 5.

### Example 22: Mixing global and per-axis limits

:::{multi-plot}
functions: x**2, sin(x), exp(x), x**3
function-names: f, g, h, p
rows: 2
cols: 2
xmin: -5
xmax: 5
ymax: 10, 3
ymin: -1, (2, 1)
ymax: 3, (2, 1)
:::

Sets global x limits (-5 to 5) for all axes, custom ymax for axis 3, and custom y range for axis at row 2, col 1.
