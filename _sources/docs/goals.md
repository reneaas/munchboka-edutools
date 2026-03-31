# `goals` directive

The `goals` directive creates a learning-goals admonition. It is styled to highlight the objectives at the beginning of a section or chapter.

## Basic usage

````markdown
:::{goals} Learning goals
- Explain slope
- Compute simple derivatives
:::
````

:::{goals} Learning goals
- Explain slope
- Compute simple derivatives
:::

## Syntax overview

```
:::{goals} Title text
- Goal 1
- Goal 2
:::
```

The first argument is the **title** (required). The body typically contains a bulleted list of goals.

## Options

_No options._

## Source

[`src/munchboka_edutools/directives/admonitions.py`](https://github.com/reneaas/munchboka-edutools/blob/main/src/munchboka_edutools/directives/admonitions.py)
