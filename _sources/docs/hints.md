# `hints` directive

The `hints` directive creates a hints admonition that is collapsed by default. Students can expand it when they need help.

## Basic usage

````markdown
:::{hints}
Start by factoring out the common term.
:::
````

:::{hints}
Start by factoring out the common term.
:::

## With custom title

````markdown
:::{hints} Hint 1
Try substituting $x = 2$.
:::
````

:::{hints} Hint 1
Try substituting $x = 2$.
:::

## Options

| Option | Meaning | Default |
|---|---|---|
| `dropdown` | Control dropdown behavior. Use `"open"` to start expanded. | collapsed |

## Source

[`src/munchboka_edutools/directives/admonitions.py`](https://github.com/reneaas/munchboka-edutools/blob/main/src/munchboka_edutools/directives/admonitions.py)
