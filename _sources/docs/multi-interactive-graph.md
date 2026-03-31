# `multi-interactive-graph` directive

The `multi-interactive-graph` directive creates multiple synchronized interactive graphs that share a single slider. This is useful for comparing how different functions respond to the same parameter.

## Basic usage

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

## Syntax overview

The container directive specifies the shared `interactive-var` and grid layout. Each nested `interactive-graph` defines one panel.

## Options

| Option | Meaning | Default |
|---|---|---|
| `interactive-var` | Shared slider variable: `name, min, max, frames` | *(required)* |
| `rows` | Number of grid rows | `1` |
| `cols` | Number of grid columns | `1` |
| `width` | CSS width of the container | — |
| `height` | CSS height | — |
| `align` | `left`, `center`, or `right` | — |
| `class` | Extra CSS classes | — |
| `name` | Stable anchor / reference name | — |

## Tips

- All nested graphs share the same slider — moving it updates every panel simultaneously.
- Each nested `interactive-graph` can define its own axis limits, functions, and drawing primitives.

## Source

[`src/munchboka_edutools/directives/multi_interactive_graph.py`](https://github.com/reneaas/munchboka-edutools/blob/main/src/munchboka_edutools/directives/multi_interactive_graph.py)
