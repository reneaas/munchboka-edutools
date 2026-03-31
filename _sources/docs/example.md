# `example` directive

The `example` directive creates a styled worked-example admonition. It visually highlights a complete solution or demonstration for students.

## Basic usage

````markdown
:::{example} Solve a quadratic
Factor $x^2-5x+6=(x-2)(x-3)$.
:::
````

:::{example} Solve a quadratic
Factor $x^2-5x+6=(x-2)(x-3)$.
:::

## Syntax overview

```
:::{example} Title text
Body content with math, lists, etc.
:::
```

The first argument is the **title** (required). The body can contain any MyST content including math, lists, nested directives, etc.

## Options

_No options._

## Source

[`src/munchboka_edutools/directives/admonitions.py`](https://github.com/reneaas/munchboka-edutools/blob/main/src/munchboka_edutools/directives/admonitions.py)
