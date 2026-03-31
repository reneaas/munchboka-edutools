# `signchart` directive

The `signchart` directive generates a sign chart for a function, showing where it is positive, negative, and zero.

## Basic usage

````markdown
```{signchart}
---
function: x**2 - 4, f(x)
factors: true
width: 80%
---
```
````

```{signchart}
---
function: x**2 - 4, f(x)
factors: true
width: 80%
---
```

## Syntax overview

The `function` key takes an expression and an optional label separated by a comma. When `factors: true` is set, the chart also shows the sign of each factor.

## Options

| Option | Meaning | Default |
|---|---|---|
| `function` | Function expression and optional label (e.g. `x**2 - 4, f(x)`) | *(required)* |
| `factors` | Show sign rows for individual factors | `false` |
| `xmin` | Left bound of the x-axis | auto |
| `xmax` | Right bound of the x-axis | auto |
| `width` | CSS width | — |
| `align` | `left`, `center`, or `right` | — |
| `class` | Extra CSS classes | — |
| `name` | Stable anchor / reference name | — |
| `alt` | Alt text | — |
| `nocache` | Force regeneration | — |
| `debug` | Keep debug output | — |

## Notes

- Aliases: `sign-chart`
- For broader function support (trig, rational, etc.), see [`signchart-2`](signchart-2.md).

## Source

[`src/munchboka_edutools/directives/signchart.py`](https://github.com/reneaas/munchboka-edutools/blob/main/src/munchboka_edutools/directives/signchart.py)
