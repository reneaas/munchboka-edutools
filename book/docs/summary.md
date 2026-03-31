# `summary` directive

The `summary` directive creates a chapter/section summary admonition, styled to highlight key takeaways.

## Basic usage

````markdown
:::{summary} Key points
- Derivative = rate of change
- Integral = accumulation
:::
````

:::{summary} Key points
- Derivative = rate of change
- Integral = accumulation
:::

## Syntax overview

```
:::{summary} Title text
- Key point 1
- Key point 2
:::
```

The first argument is the **title** (required). The body typically contains a bulleted list of key points.

## Options

_No options._

## Source

[`src/munchboka_edutools/directives/admonitions.py`](https://github.com/reneaas/munchboka-edutools/blob/main/src/munchboka_edutools/directives/admonitions.py)
