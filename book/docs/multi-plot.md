# `multi-plot` directive

The `multi-plot` directive builds a grid of static plots from a list of function expressions. All plots share the same axis limits and styling.

## Basic usage

````markdown
:::{multi-plot}
functions: [x**2, sin(x), exp(x)]
rows: 1
cols: 3
xmin: -3
xmax: 3
width: 100%
:::
````

:::{multi-plot}
functions: [x**2, sin(x), exp(x)]
rows: 1
cols: 3
xmin: -3
xmax: 3
width: 100%
:::

## Syntax overview

The `functions` key accepts a Python-style list of expressions. Each expression gets its own subplot in the grid.

## Options

| Option | Meaning | Default |
|---|---|---|
| `functions` | List of function expressions (e.g. `[x**2, sin(x)]`) | *(required)* |
| `fn_labels` / `function-names` | Display labels for the functions | auto |
| `rows` | Number of grid rows | auto |
| `cols` | Number of grid columns | auto |
| `domains` | Per-function x-ranges | — |
| `xmin`, `xmax`, `ymin`, `ymax` | Shared axis limits | auto |
| `xstep`, `ystep` | Tick spacing | auto |
| `fontsize` | Font size | — |
| `lw` | Line width | — |
| `alpha` | Line alpha | — |
| `grid` | Show grid lines | — |
| `ticks` | Show ticks | — |
| `width` | CSS width | — |
| `align` | `left`, `center`, or `right` | — |
| `vlines`, `hlines`, `lines` | Drawing primitives shared across panels | — |
| `points`, `point` | Points shared across panels | — |
| `text` | Text annotations shared across panels | — |
| `annotate` | Arrow annotations shared across panels | — |
| `tangent` | Tangent lines shared across panels | — |
| `class` | Extra CSS classes | — |
| `name` | Stable anchor / reference name | — |
| `alt` | Alt text | — |
| `nocache` | Force regeneration | — |
| `debug` | Keep debug output | — |

## Notes

- Aliases: `multiplot`

## Source

[`src/munchboka_edutools/directives/multi_plot.py`](https://github.com/reneaas/munchboka-edutools/blob/main/src/munchboka_edutools/directives/multi_plot.py)
