# `signchart-2` directive

The `signchart-2` directive generates an enhanced sign chart with broader function support — including trigonometric, rational, and transcendental functions. It also supports custom domains and styling.

## Basic usage

````markdown
```{signchart-2}
---
function: sin(x)*cos(x), f(x)
domain: (-3.5, 3.5)
factors: true
width: 100%
---
```
````

```{signchart-2}
---
function: sin(x)*cos(x), f(x)
domain: (-3.5, 3.5)
factors: true
width: 100%
---
```

## Options

| Option | Meaning | Default |
|---|---|---|
| `function` | Function expression and optional label | *(required)* |
| `factors` | Show sign rows for individual factors | `false` |
| `domain` | Restrict the analysis to a domain, e.g. `(-3.5, 3.5)` | auto |
| `color` | Customize sign colors | default |
| `generic_labels` | Use generic ($+$/$-$) labels instead of factor names | `false` |
| `fontsize` | Font size | auto |
| `figsize` | Matplotlib figure size | auto |
| `small_figsize` | Use a compact layout | — |
| `labelpad` | Padding for labels | auto |
| `width` | CSS width | — |
| `align` | `left`, `center`, or `right` | — |
| `class` | Extra CSS classes | — |
| `name` | Stable anchor / reference name | — |
| `alt` | Alt text | — |
| `nocache` | Force regeneration | — |
| `debug` | Keep debug output | — |

## Notes

- Aliases: `signchart2`
- For polynomial-only sign charts, the simpler [`signchart`](signchart.md) may suffice.

## Source

[`src/munchboka_edutools/directives/signchart2.py`](https://github.com/reneaas/munchboka-edutools/blob/main/src/munchboka_edutools/directives/signchart2.py)
