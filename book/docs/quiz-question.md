# `quiz-question` directive

Defines a question block inside `quiz-2`.

## Signature

- Required arguments: `0`
- Optional arguments: `0`
- Body content: `yes`

## Options

_No options._

## Example

````markdown
::::{quiz-question}
Compute $2+2$.

:::{quiz-answer}
:correct:
4
:::

:::{quiz-answer}
5
:::
::::
````

## Notes

- Must be nested inside `quiz-2`.

## Source

`src/munchboka_edutools/directives/quiz2.py`
