# Multi-Plot2 Test

This page tests the new `multi-plot2` directive.

## Example 1: Simple 2×2 Grid

::::{multi-plot2}
---
rows: 2
cols: 2
---

:::{plot}
function: x**2, f, blue
:::

:::{plot}
function: exp(-x), g, red
:::

:::{plot}
function: sin(x), h, green
:::

:::{plot}
function: x*cos(x)
:::

::::

## Example 2: Using text keyword

::::{multi-plot2}
---
rows: 1
cols: 2
---

:::{plot}
x_min: -2
x_max: 2
y_min: -2
y_max: 2
function: x**2, f, blue
text:
  - text: "Parabola"
    x: 0
    y: 1.5
    color: blue
:::

:::{plot}
x_min: -2
x_max: 2
y_min: -2
y_max: 2
function: -x**2, g, red
text:
  - text: "Inverted Parabola"
    x: 0
    y: -1.5
    color: red
:::

::::

## Example 3: With annotations

::::{multi-plot2}
---
rows: 1
cols: 2
---

:::{plot}
x_min: -3
x_max: 3
y_min: -3
y_max: 3
function: x**2, f, blue
annotate:
  - text: "Minimum"
    xy: [0, 0]
    xytext: [1, 1]
    color: blue
:::

:::{plot}
x_min: -3
x_max: 3
y_min: -3
y_max: 3
function: x**3, g, red
annotate:
  - text: "Origin"
    xy: [0, 0]
    xytext: [1.5, -1.5]
    color: red
:::

::::
