# `theory` directive

The `theory` directive creates a theory/concept admonition, styled to present definitions, theorems, or key concepts.

## Basic usage

````markdown
:::{theory} The chain rule
If $y=f(g(x))$, then $y' = f'(g(x))g'(x)$.
:::
````

:::{theory} The chain rule
If $y=f(g(x))$, then $y' = f'(g(x))g'(x)$.
:::

## Syntax overview

```
:::{theory} Title text
Body content with math, definitions, etc.
:::
```

The first argument is the **title** (required). The body can contain any MyST content.

## Options

_No options._

## Source

[`src/munchboka_edutools/directives/admonitions.py`](https://github.com/reneaas/munchboka-edutools/blob/main/src/munchboka_edutools/directives/admonitions.py)
