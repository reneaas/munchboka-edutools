# Pair Puzzle Examples

The `pair-puzzle` directive creates interactive drag-and-drop matching games where users pair related items.

## Basic Example

Match mathematical expressions with their simplified forms:

:::{pairpuzzle}
$x^2 + 2x + 1$ : $(x+1)^2$
$x^2 - 1$ : $(x-1)(x+1)$
$2x + 4$ : $2(x+2)$
:::

## Text Matching

Match concepts with definitions:

:::{pairpuzzle}
Derivative : Rate of change
Integral : Area under curve
Limit : Approaching value
:::

## Mixed Content

Mix text, math, and HTML:

:::{pairpuzzle}
Pythagorean theorem : $a^2 + b^2 = c^2$
Circle area : $\pi r^2$
Quadratic formula : $x = \frac{-b \pm \sqrt{b^2-4ac}}{2a}$
:::

## Trigonometric Identities

Match trigonometric expressions:

:::{pairpuzzle}
$\sin^2(x) + \cos^2(x)$ : $1$
$\tan(x)$ : $\frac{\sin(x)}{\cos(x)}$
$\sin(2x)$ : $2\sin(x)\cos(x)$
$\cos(2x)$ : $\cos^2(x) - \sin^2(x)$
:::

## With Custom Class

You can add custom CSS classes:

:::{pairpuzzle}
:class: my-custom-class

First pair left : First pair right
Second pair left : Second pair right
:::

## How It Works

- Drag items from the top container to the drop zones below
- Each drop zone should contain exactly two items that form a matching pair
- Click "Sjekk svaret!" to check your answer
- Correct pairs turn green, incorrect ones turn red
- Use "Reset puslespill" to start over

## Features

- **LaTeX Math Support**: Uses KaTeX for rendering mathematical expressions
- **Drag and Drop**: Intuitive drag-and-drop interface
- **Instant Feedback**: Color-coded feedback (green for correct, red for incorrect)
- **Theme Support**: Automatically adapts to light/dark mode
- **Multiple Puzzles**: Can have multiple puzzles on the same page
