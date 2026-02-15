# `quiz` directive

Creates an interactive multiple-choice quiz from a text format.

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
:::{quiz}
Q: What is $2+2$?
+ 4
- 3
- 5

Q: What is $3\times 3$?
+ 9
- 6
- 12
:::
````

## Source

`src/munchboka_edutools/directives/quiz.py`
