# `multi-plot2` directive

The `multi-plot2` directive arranges nested `plot` blocks in a grid layout. Unlike `multi-plot` (which takes a list of function expressions), `multi-plot2` gives each subplot its own full `plot` directive — allowing different drawing primitives, styles, and overlays per panel.

## Basic usage

````markdown
:::::{multi-plot2}
---
rows: 1
cols: 2
---

:::{plot}
function: x**2, f
:::

:::{plot}
function: x**3, g
:::
:::::
````

:::::{multi-plot2}
---
rows: 1
cols: 2
---

:::{plot}
function: x**2, f
:::

:::{plot}
function: x**3, g
:::
:::::

## Syntax overview

The container specifies the grid dimensions and shared styling. Each nested `plot` is a full plot directive.

## Options

### Container options

| Option | Meaning | Default |
|---|---|---|
| `rows` | Number of grid rows | `1` |
| `cols` | Number of grid columns | `1` |
| `width` | CSS width of the combined figure | — |
| `align` | `left`, `center`, or `right` | — |

### Shared defaults (applied to all nested plots)

| Option | Meaning |
|---|---|
| `xmin`, `xmax`, `ymin`, `ymax` | Axis limits |
| `xstep`, `ystep` | Tick spacing |
| `fontsize` | Font size |
| `ticks`, `grid` | Ticks and grid |
| `lw`, `alpha` | Line width and alpha |
| `figsize` | Figure size |
| `xlabel`, `ylabel` | Axis labels |
| `usetex` | LaTeX text rendering |
| `axis` | Axis style |

### Other options

| Option | Meaning |
|---|---|
| `class` | Extra CSS classes |
| `name` | Stable anchor / reference name |
| `alt` | Alt text |
| `nocache` | Force regeneration |
| `debug` | Keep debug output |

## Tips

- Shared options set on the container are inherited by all nested `plot` blocks but can be overridden per subplot.
- Use `multi-plot` when all subplots share the same structure and only differ by function expression.

## Source

[`src/munchboka_edutools/directives/multi_plot2.py`](https://github.com/reneaas/munchboka-edutools/blob/main/src/munchboka_edutools/directives/multi_plot2.py)
