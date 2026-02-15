# `quiz-2` directive

Container directive for nested Quiz 2.0 questions/answers.

## Signature

- Required arguments: `0`
- Optional arguments: `0`
- Body content: `yes`

## Options

| Option | Type |
|---|---|
| `shuffle` | flag |

## Example

````markdown
:::::{quiz-2}
::::{quiz-question}
What is $2+2$?

:::{quiz-answer}
:correct:
4
:::

:::{quiz-answer}
3
:::
::::
:::::
````

## Source

`src/munchboka_edutools/directives/quiz2.py`
