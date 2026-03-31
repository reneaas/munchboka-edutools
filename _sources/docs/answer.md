# `answer` directive

The `answer` directive creates a styled admonition for displaying answers to problems. By default it is collapsed (dropdown) so students can reveal the answer when ready.

## Basic usage

````markdown
:::{answer}
$x = 3$
:::
````

which yields:

:::{answer}
$x = 3$
:::

## Custom title

You can provide a custom title as the directive argument:

````markdown
:::{answer} Solution to Exercise 1
$f'(x) = 2x - 3$, so $f'(x) = 0$ gives $x = \frac{3}{2}$.
:::
````

which yields:

:::{answer} Solution to Exercise 1
$f'(x) = 2x - 3$, so $f'(x) = 0$ gives $x = \frac{3}{2}$.
:::

## Expanded by default

Set `dropdown: 0` to show the answer expanded instead of collapsed:

````markdown
:::{answer} Quick check
:dropdown: 0
The answer is 42.
:::
````

which yields:

:::{answer} Quick check
:dropdown: 0
The answer is 42.
:::

## Options

| Option | Meaning |
|---|---|
| `dropdown` | `1` (default) to collapse, `0` to expand |

## Source

The implementation lives in `src/munchboka_edutools/directives/admonitions.py`.
