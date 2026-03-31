# `flashcards` directive

The `flashcards` directive creates an interactive flashcard deck. Students click to flip cards and navigate through the deck.

## Basic usage

````markdown
:::{flashcards}
Q: Derivative of $x^2$
A: $2x$

Q: Derivative of $\sin(x)$
A: $\cos(x)$
:::
````

:::{flashcards}
Q: Derivative of $x^2$
A: $2x$

Q: Derivative of $\sin(x)$
A: $\cos(x)$
:::

## Syntax overview

Cards are written as `Q:` / `A:` pairs separated by blank lines, just like the quiz format. Each card has a question side and an answer side.

## Options

| Option | Meaning | Default |
|---|---|---|
| `shuffle` | Randomize card order on each page load | off |
| `show_progress` | Show card counter (e.g. "3 / 10") | on |
| `start_index` | Zero-based index of the first card to show | `0` |

## Source

[`src/munchboka_edutools/directives/flashcards.py`](https://github.com/reneaas/munchboka-edutools/blob/main/src/munchboka_edutools/directives/flashcards.py)
