# `solution` directive

The `solution` directive creates a full-solution admonition that is collapsed by default. Students expand it to see the solution.

## Basic usage

````markdown
:::{solution}
Step 1: Set up the equation.

Step 2: Solve for $x$.
:::
````

:::{solution}
Step 1: Set up the equation.

Step 2: Solve for $x$.
:::

## With custom title

````markdown
:::{solution} Full solution
$$
x = \frac{-b \pm \sqrt{b^2 - 4ac}}{2a}
$$
:::
````

:::{solution} Full solution
$$
x = \frac{-b \pm \sqrt{b^2 - 4ac}}{2a}
$$
:::

## Options

| Option | Meaning | Default |
|---|---|---|
| `dropdown` | Control dropdown behavior. Use `"open"` to start expanded. | collapsed |

## Source

[`src/munchboka_edutools/directives/admonitions.py`](https://github.com/reneaas/munchboka-edutools/blob/main/src/munchboka_edutools/directives/admonitions.py)
