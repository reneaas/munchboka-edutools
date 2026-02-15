# `multi-interactive-graph` directive

Creates multiple synchronized interactive graphs with one shared slider.

## Signature

- Required arguments: `0`
- Optional arguments: `0`
- Body content: `yes`

## Options

| Option | Type |
|---|---|
| `interactive-var` | string |
| `rows` | string |
| `cols` | string |
| `width` | string |
| `height` | string |
| `align` | string |
| `class` | string |
| `name` | string |

## Example

````markdown
:::::{multi-interactive-graph}
---
interactive-var: a, 0, 4, 21
rows: 1
cols: 2
---

:::{interactive-graph}
function: sin(a*x)
xmin: -6
xmax: 6
:::

:::{interactive-graph}
function: cos(a*x)
xmin: -6
xmax: 6
:::
:::::
````

## Source

`src/munchboka_edutools/directives/multi_interactive_graph.py`
