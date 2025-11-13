# Custom Admonitions

The custom admonition directives provide styled content blocks for educational materials.

## Theory

For presenting theoretical content:

:::{theory} Pythagoras' Theorem
For a right triangle with sides $a$ and $b$ and hypotenuse $c$:

$$a^2 + b^2 = c^2$$

This fundamental relation has been known since ancient times.
:::

## Example

For worked examples:

:::{example} Solving a Quadratic Equation
Solve: $x^2 - 5x + 6 = 0$

Using the quadratic formula:
$$x = \frac{5 \pm \sqrt{25 - 24}}{2} = \frac{5 \pm 1}{2}$$

So $x = 3$ or $x = 2$
:::

## Exercise

For student exercises:

:::{exercise} Practice Problem
Find the derivative of $f(x) = x^3 + 2x^2 - 5x + 1$.
:::

## Explore

For exploratory activities:

:::{explore} Investigation
Try different values and observe the pattern:
- What happens when $x = 0$?
- What happens when $x$ is very large?
- Can you find a general rule?
:::

## Goals

For learning objectives and goals:

:::{goals} Learning Objectives
After this section, you should be able to:
- Understand the concept of derivatives
- Apply the chain rule
- Solve optimization problems
:::

## Summary

For section summaries:

:::{summary} Key Points
- Derivatives measure rate of change
- Integration finds area under curves
- The fundamental theorem connects them
:::

## Hints

For providing hints (default collapsed):

:::{hints}
Start by factoring out the common term.
:::

:::{hints} Custom Hint Title
:dropdown: 0

This hint is always visible.
:::

## Answer

For short answers (default collapsed):

:::{answer}
$x = 42$
:::

:::{answer} Answer to Question 2
The solution is $y = 2x + 3$.
:::

## Solution

For full solutions (default collapsed):

:::{solution}
**Step 1**: Write down what we know
- Initial velocity: $v_0 = 0$
- Acceleration: $a = 9.8$ m/s²
- Time: $t = 3$ s

**Step 2**: Apply the formula
$$v = v_0 + at = 0 + 9.8 \times 3 = 29.4 \text{ m/s}$$

**Answer**: The final velocity is 29.4 m/s.
:::

:::{solution} Alternative Method
:dropdown: 0

This solution is always visible.

You can also solve this using energy conservation...
:::

## Nested Admonitions

You can nest admonitions within each other:

:::{exercise} Challenge Problem
Prove that $\sqrt{2}$ is irrational.

:::{hints}
Use proof by contradiction. Assume $\sqrt{2} = \frac{p}{q}$ where $p$ and $q$ are coprime integers.
:::

:::{solution}
**Proof by contradiction:**

Assume $\sqrt{2} = \frac{p}{q}$ where $p$ and $q$ are coprime...

[Rest of proof here]

**Conclusion**: This contradicts our assumption, so $\sqrt{2}$ is irrational.
:::
:::

## Features

All these admonitions support:
- **LaTeX math**: Both inline $x^2$ and display $$\int_0^1 x dx$$
- **Markdown**: Including **bold**, *italic*, and `code`
- **Dropdown**: Optional collapsible sections
- **Theme awareness**: Adapts to light/dark mode with custom icons
- **Custom titles**: Most directives allow custom titles
- **MyST syntax**: Full support for colon-fence syntax (:::)
