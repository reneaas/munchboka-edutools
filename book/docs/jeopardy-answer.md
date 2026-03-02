# `jeopardy-answer` directive

Defines or overrides the answer for a Jeopardy 2.0 tile.

## Signature

- Required arguments: `0`
- Optional arguments: `0`
- Body content: `yes`

## Options

| Option | Type |
|---|---|
| `category` | string |
| `points` | positive integer |

## Example

````markdown
::::{jeopardy-answer}
---
category: Functions
points: 200
---
The vertex is $(1,0)$.
::::
````

Nested inside a question (no need to repeat `category`/`points`):

````markdown
::::{jeopardy-question}
---
category: Functions
points: 200
---
Find the vertex of $y=(x-1)^2$.

:::{jeopardy-answer}
The vertex is $(1,0)$.
:::
::::
````

## Notes

- Must be nested inside `jeopardy-2`.
- If nested inside `jeopardy-question`, `category` and `points` are inherited from the parent question (so you don't have to repeat them).
- If used directly under `jeopardy-2` (not inside a question), you should provide `category` + `points` so it can be matched to the correct tile.

## Source

`src/munchboka_edutools/directives/jeopardy2.py`
