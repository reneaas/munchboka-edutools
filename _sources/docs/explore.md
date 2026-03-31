# `explore` directive

The `explore` directive creates an exploratory activity admonition. It visually signals an open-ended investigation or discovery task.

## Basic usage

````markdown
:::{explore} Investigate
Try several values of $x$ and describe the pattern.
:::
````

:::{explore} Investigate
Try several values of $x$ and describe the pattern.
:::

## Syntax overview

```
:::{explore} Title text
Body content.
:::
```

The first argument is the **title** (required). The body can contain any MyST content.

## Options

_No options._

## Source

[`src/munchboka_edutools/directives/admonitions.py`](https://github.com/reneaas/munchboka-edutools/blob/main/src/munchboka_edutools/directives/admonitions.py)
