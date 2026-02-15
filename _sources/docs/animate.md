# `animate` directive

Renders an animated graph by varying one or more variables over frames.

## Signature

- Required arguments: `0`
- Optional arguments: `0`
- Body content: `yes`

## Options

| Option | Type |
|---|---|
| `animate-var` | string |
| `fps` | positive integer |
| `duration` | positive integer |
| `loop` | value |
| `format` | value |
| `function` | string |
| `functions` | string |
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
:::{animate}
animate-var: a, 1, 5, 20
fps: 10
function: sin(a*x)
xmin: -8
xmax: 8
ymin: -2
ymax: 2
grid: true
:::
````

## Notes

- Supports the same plotting primitives/options as `plot` plus animation controls.

## Source

`src/munchboka_edutools/directives/animate.py`
