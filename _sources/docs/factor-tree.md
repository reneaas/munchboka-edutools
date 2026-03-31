# `factor-tree` directive

The `factor-tree` directive generates a factor-tree figure for a given integer, showing its prime factorisation as a tree structure.

## Basic usage

````markdown
```{factor-tree}
:n: 84
:width: 70%
```
````

```{factor-tree}
:n: 84
:width: 70%
```

## Syntax overview

The integer to factorize is specified with the `:n:` option. The figure is rendered as an inline SVG.

## Options

| Option | Meaning | Default |
|---|---|---|
| `n` | The integer to factorize | *(required)* |
| `width` | CSS width (e.g. `70%`, `400px`) | — |
| `align` | `left`, `center`, or `right` | — |
| `angle` | Angle between branches (degrees) | auto |
| `branch_length` | Length of tree branches | auto |
| `fontsize` | Font size for numbers | auto |
| `figsize` | Matplotlib figure size, e.g. `(6, 4)` | auto |
| `figwidth` | Figure width | — |
| `figheight` | Figure height | — |
| `class` | Extra CSS classes | — |
| `name` | Stable anchor / reference name | — |
| `alt` | Alt text for accessibility | — |
| `nocache` | Force regeneration | — |
| `debug` | Keep debug output | — |

## Source

[`src/munchboka_edutools/directives/factor_tree.py`](https://github.com/reneaas/munchboka-edutools/blob/main/src/munchboka_edutools/directives/factor_tree.py)
