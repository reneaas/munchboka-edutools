# `multi-plot2` directive

Container directive that arranges nested `plot` blocks in a grid.

## Signature

- Required arguments: `0`
- Optional arguments: `0`
- Body content: `yes`

## Options

| Option | Type |
|---|---|
| `rows` | positive integer |
| `cols` | positive integer |
| `width` | length / percentage |
| `align` | value |
| `class` | CSS class list |
| `name` | string |
| `xmin` | string |
| `xmax` | string |
| `ymin` | string |
| `ymax` | string |
| `xstep` | string |
| `ystep` | string |
| `fontsize` | string |
| `ticks` | string |
| `grid` | string |
| `xticks` | string |
| `yticks` | string |
| `lw` | string |
| `alpha` | string |
| `figsize` | string |
| `xlabel` | string |
| `ylabel` | string |
| `usetex` | string |
| `axis` | string |
| `alt` | string |
| `nocache` | flag |
| `debug` | flag |

## Example

````markdown
:::::{multi-plot2}
:rows: 1
:cols: 2

:::{plot}
function: x**2
:::

:::{plot}
function: x**3
:::
:::::
````

## Source

`src/munchboka_edutools/directives/multi_plot2.py`
