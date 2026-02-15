# `multiplot` directive

`multiplot` is an alias for [`multi-plot`](multi-plot.md).

Builds a grid of static plots from a list of functions.

## Example

````markdown
:::{multiplot}
functions: [x**2, sin(x), exp(x)]
rows: 1
cols: 3
xmin: -3
xmax: 3
width: 100%
:::
````

Use the canonical page for full details: [`multi-plot`](multi-plot.md).
