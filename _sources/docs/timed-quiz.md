# `timed-quiz` directive

Creates a timed multiple-choice quiz with countdown and scoring.

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
:::{timed-quiz}
Q: What is $5-2$?
+ 3
- 2
- 4

Q: What is $2^3$?
+ 8
- 6
- 9
:::
````

## Notes

- Aliases: `timedquiz`

## Source

`src/munchboka_edutools/directives/timed_quiz.py`
