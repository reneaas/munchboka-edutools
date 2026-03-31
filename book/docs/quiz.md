# `quiz` directive

The `quiz` directive creates an interactive multiple-choice quiz from a simple text format, using `+` and `-` to mark correct and incorrect answers.

## Basic usage

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

## Syntax overview

```
Q: <question text>
+ <correct answer>
- <wrong answer>
- <wrong answer>
```

- **`Q:`** — starts a new question
- **`+`** — marks a correct answer
- **`-`** — marks an incorrect answer

Questions are separated by blank lines. Multiple correct answers are allowed.

## Options

| Option | Meaning | Default |
|---|---|---|
| `shuffle` | Randomize answer order on each page load | off |

## Notes

- For richer questions with embedded directives, see [`quiz-2`](quiz-2.md).

## Source

[`src/munchboka_edutools/directives/quiz.py`](https://github.com/reneaas/munchboka-edutools/blob/main/src/munchboka_edutools/directives/quiz.py)
