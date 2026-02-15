# `interactive-graph` directive

Creates a slider-driven interactive graph from pre-rendered frames.

## Signature

- Required arguments: `0`
- Optional arguments: `0`
- Body content: `yes`

## Options

| Option | Type |
|---|---|
| `interactive-var` | string |
| `interactive-max-frames` | non-negative integer |
| `width` | length / percentage |
| `height` | string |
| `align` | value |
| `class` | CSS class list |
| `alt` | string |
| `name` | string |
| `caption` | string |
| `nocache` | flag |
| `debug` | flag |
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
:::{interactive-graph}
interactive-var: a, -3, 3, 31
function: x**2 + a*x
xmin: -6
xmax: 6
ymin: -10
ymax: 10
grid: true
:::
````

## Notes

- Supports repeated `interactive-var:` lines for multi-variable sliders.

## Source

`src/munchboka_edutools/directives/interactive_graph.py`
