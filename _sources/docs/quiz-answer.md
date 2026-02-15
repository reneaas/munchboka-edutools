# `quiz-answer` directive

Defines one answer option inside `quiz-question`.

## Signature

- Required arguments: `0`
- Optional arguments: `0`
- Body content: `yes`

## Options

| Option | Type |
|---|---|
| `correct` | flag |

## Example

````markdown
:::{quiz-answer}
:correct:
The correct option text
:::
````

## Notes

- Must be nested inside `quiz-question`.

## Source

`src/munchboka_edutools/directives/quiz2.py`
