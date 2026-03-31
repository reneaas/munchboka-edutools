# `timed-quiz` directive

The `timed-quiz` directive creates a timed multiple-choice quiz with countdown and scoring. It uses the same `Q:`/`+`/`-` format as the `quiz` directive but adds a timer.

## Basic usage

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

## Syntax overview

The content format is identical to the [`quiz`](quiz.md) directive:

```
Q: <question text>
+ <correct answer>
- <wrong answer>
```

The timer counts how long the student takes. A score is displayed at the end.

## Options

| Option | Meaning | Default |
|---|---|---|
| `shuffle` | Randomize question and answer order | off |

## Notes

- Aliases: `timedquiz`

## Source

[`src/munchboka_edutools/directives/timed_quiz.py`](https://github.com/reneaas/munchboka-edutools/blob/main/src/munchboka_edutools/directives/timed_quiz.py)
