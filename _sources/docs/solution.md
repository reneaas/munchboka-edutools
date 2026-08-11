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

## With timer

Use `timer` to delay the solution button. The value is in minutes.

````markdown
:::{solution}
---
timer: 5
---
Step 1: Try the problem before opening the solution.
:::
````

:::{solution}
---
timer: 5
---
Step 1: Try the problem before opening the solution.
:::

## Options

| Option | Meaning | Default |
|---|---|---|
| `dropdown` | Control dropdown behavior. Use `"open"` to start expanded. | collapsed |
| `timer` | Optional button-lock timer in minutes. | no timer |

## Source

[`src/munchboka_edutools/directives/admonitions.py`](https://github.com/reneaas/munchboka-edutools/blob/main/src/munchboka_edutools/directives/admonitions.py)
