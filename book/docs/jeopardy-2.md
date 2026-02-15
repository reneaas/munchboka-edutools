# `jeopardy-2` directive

Container directive for nested Jeopardy 2.0 question/answer blocks.

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
:::::{jeopardy-2}
::::{jeopardy-question}
---
category: Algebra
points: 100
---
What is $2+2$?
Answer: 4
::::
:::::
````

## Source

`src/munchboka_edutools/directives/jeopardy2.py`
