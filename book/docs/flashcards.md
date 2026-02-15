# `flashcards` directive

Creates an interactive flashcard deck.

## Signature

- Required arguments: `0`
- Optional arguments: `0`
- Body content: `yes`

## Options

| Option | Type |
|---|---|
| `shuffle` | flag |
| `show_progress` | flag |
| `start_index` | non-negative integer |

## Example

````markdown
:::{flashcards}
Q: Derivative of $x^2$
A: $2x$

Q: Derivative of $\sin(x)$
A: $\cos(x)$
:::
````

## Source

`src/munchboka_edutools/directives/flashcards.py`
