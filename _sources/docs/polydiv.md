# `polydiv` directive

The `polydiv` directive renders a polynomial long-division layout as an SVG figure. It supports step-by-step reveal and custom variable names.

## Basic usage

````markdown
:::{polydiv}
:p: x^3 - 3x^2 + 1
:q: x - 1
:width: 80%
:::
````

:::{polydiv}
:p: x^3 - 3x^2 + 1
:q: x - 1
:width: 80%
:::

## Step-by-step reveal

Use `stage` to show only the first *n* steps of the division:

````markdown
:::{polydiv}
:p: x^3 - 3x^2 + 1
:q: x - 1
:stage: 2
:width: 80%
:::
````

:::{polydiv}
:p: x^3 - 3x^2 + 1
:q: x - 1
:stage: 2
:width: 80%
:::

## Options

| Option | Meaning | Default |
|---|---|---|
| `p` | Dividend polynomial | *(required)* |
| `q` | Divisor polynomial | *(required)* |
| `stage` | Number of steps to reveal (0 = all) | `0` |
| `vars` | Variable name (e.g. `t` instead of `x`) | `x` |
| `inline` | Render inline (no figure wrapper) | off |
| `width` | CSS width | — |
| `align` | `left`, `center`, or `right` | — |
| `class` | Extra CSS classes | — |
| `name` | Stable anchor / reference name | — |
| `alt` | Alt text | — |
| `nocache` / `cache` | Force regeneration / enable caching | — |

## Source

[`src/munchboka_edutools/directives/polydiv.py`](https://github.com/reneaas/munchboka-edutools/blob/main/src/munchboka_edutools/directives/polydiv.py)
