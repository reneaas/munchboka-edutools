# `multi-plot` directive

Builds a grid of static plots from a list of functions.

## Signature

- Required arguments: `0`
- Optional arguments: `0`
- Body content: `yes`

## Options

| Option | Type |
|---|---|
| `functions` | string (required) |
| `fn_labels` | string |
| `function-names` | string |
| `domains` | string |
| `vlines` | string |
| `hlines` | string |
| `xlims` | string |
| `ylims` | string |
| `lines` | string |
| `points` | string |
| `point` | string |
| `hline` | string |
| `vline` | string |
| `line` | string |
| `tangent` | string |
| `xmin` | string |
| `xmax` | string |
| `ymin` | string |
| `ymax` | string |
| `text` | string |
| `annotate` | string |
| `xstep` | string |
| `ystep` | string |
| `fontsize` | string |
| `lw` | string |
| `alpha` | string |
| `grid` | string |
| `ticks` | string |
| `rows` | string |
| `cols` | string |
| `align` | value |
| `class` | CSS class list |
| `name` | string |
| `nocache` | flag |
| `alt` | string |
| `width` | length / percentage |
| `debug` | flag |

## Example

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

## Notes

- Aliases: `multiplot`

## Source

`src/munchboka_edutools/directives/multi_plot.py`
