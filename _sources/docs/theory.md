# `theory` directive

Creates a theory/concept admonition.

## Signature

- Required arguments: `1`
- Optional arguments: `0`
- Body content: `yes`

## Options

_No options._

## Example

````markdown
:::{theory} The chain rule
If $y=f(g(x))$, then $y' = f'(g(x))g'(x)$.
:::
````

## Source

`src/munchboka_edutools/directives/admonitions.py`
