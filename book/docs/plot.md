# `plot` directive

Renders a static mathematical figure from key-value primitives.

## Signature

- Required arguments: `0`
- Optional arguments: `0`
- Body content: `yes`

## Options

| Option | Type |
|---|---|
| `width` | length / percentage |
| `align` | value |
| `class` | CSS class list |
| `name` | string |
| `nocache` | flag |
| `debug` | flag |
| `alt` | string |
| `usetex` | string |
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
| `endpoint_markers` | string |
| `function-endpoints` | string |
| `xlabel` | string |
| `ylabel` | string |

## Example

````markdown
:::{plot}
function: x**2 - 1, f
point: (1, f(1))
xmin: -3
xmax: 3
ymin: -2
ymax: 5
grid: on
:::
````

## Notes

- Supports many primitives: `function`, `point`, `line`, `line-segment`, `polygon`, `vector`, `circle`, `ellipse`, `curve`, `text`, `annotate`, and more.

## Source

`src/munchboka_edutools/directives/plot.py`
