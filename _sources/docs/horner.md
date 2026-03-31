# `horner` directive

The `horner` directive renders a Horner (synthetic division) scheme as an SVG figure. It supports step-by-step reveal via the `stage` option.

## Basic usage

````markdown
:::{horner}
:p: x^3 + 2x^2 - 3x - 6
:x: 1
:::
````

:::{horner}
:p: x^3 + 2x^2 - 3x - 6
:x: 1
:::

## Step-by-step reveal

Use `stage` to show only the first *n* steps of the scheme, perfect for classroom walkthroughs:

````markdown
:::{horner}
:p: x^3 + 2x^2 - 3x - 6
:x: 1
:stage: 2
:::
````

:::{horner}
:p: x^3 + 2x^2 - 3x - 6
:x: 1
:stage: 2
:::

## Options

| Option | Meaning | Default |
|---|---|---|
| `p` | Polynomial expression (e.g. `x^3 + 2x^2 - 3x - 6`) | *(required)* |
| `x` | Evaluation point / divisor | *(required)* |
| `stage` | Number of steps to reveal (0 = show all) | `0` |
| `tutor` | Enable interactive tutor mode | off |
| `width` | CSS width | — |
| `align` | `left`, `center`, or `right` | — |
| `class` | Extra CSS classes | — |
| `name` | Stable anchor / reference name | — |
| `alt` | Alt text | — |
| `nocache` | Force regeneration | — |

## Source

[`src/munchboka_edutools/directives/horner.py`](https://github.com/reneaas/munchboka-edutools/blob/main/src/munchboka_edutools/directives/horner.py)
