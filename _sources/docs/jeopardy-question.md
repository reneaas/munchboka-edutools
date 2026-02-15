# `jeopardy-question` directive

Defines a Jeopardy 2.0 question tile.

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
::::{jeopardy-question}
---
category: Functions
points: 200
---
Find the vertex of $y=(x-1)^2$.
Answer: $(1,0)$
::::
````

## Notes

- Must be nested inside `jeopardy-2`.

## Source

`src/munchboka_edutools/directives/jeopardy2.py`
