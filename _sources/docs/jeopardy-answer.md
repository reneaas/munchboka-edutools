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

## Notes

- Must be nested inside `jeopardy-2` and matched by `category` + `points`.

## Source

`src/munchboka_edutools/directives/jeopardy2.py`
