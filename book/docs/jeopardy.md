# `jeopardy` directive

Creates an interactive Jeopardy board from text-based categories and tiles.

## Signature

- Required arguments: `0`
- Optional arguments: `0`
- Body content: `yes`

## Options

| Option | Type |
|---|---|
| `teams` | string |

## Example

````markdown
:::{jeopardy}
:teams: 2

Category: Algebra
100:
Q: Solve $x+2=5$.
A: $x=3$

200:
Q: Solve $2x=10$.
A: $x=5$
:::
````

## Source

`src/munchboka_edutools/directives/jeopardy.py`
