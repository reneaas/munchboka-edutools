# `exercise` directive

The `exercise` directive creates a styled exercise/task admonition. It supports difficulty levels and a digital-aids mode that changes the icon.

## Basic usage

````markdown
:::{exercise} Practice
Find the derivative of $f(x)=x^3-2x$.
:::
````

:::{exercise} Practice
Find the derivative of $f(x)=x^3-2x$.
:::

## With digital aids

When `aids: true` is set, the exercise icon changes to a computer icon, signaling that digital tools (CAS, graphing calculators, etc.) are allowed:

````markdown
:::{exercise} Calculator exercise
---
aids: true
---
Use a CAS tool to solve $x^3 - 3x + 1 = 0$.
:::
````

:::{exercise} Calculator exercise
---
aids: true
---
Use a CAS tool to solve $x^3 - 3x + 1 = 0$.
:::

## Options

| Option | Meaning | Default |
|---|---|---|
| `level` | Difficulty tag (e.g. `"easy"`, `"medium"`, `"hard"`) | — |
| `aids` | Switch to digital-aids icon: `true`/`false` | `false` |

## Source

[`src/munchboka_edutools/directives/admonitions.py`](https://github.com/reneaas/munchboka-edutools/blob/main/src/munchboka_edutools/directives/admonitions.py)
