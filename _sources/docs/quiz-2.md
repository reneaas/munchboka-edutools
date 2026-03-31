# `quiz-2` directive

The `quiz-2` directive creates an interactive quiz using nested `quiz-question` and `quiz-answer` directives. This allows rich content (plots, code, images) inside questions and answers.

## Basic usage

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

## Syntax overview

1. **`quiz-2`** — outer container
2. **`quiz-question`** — one per question; body is the question text
3. **`quiz-answer`** — one per answer choice; use `:correct:` to mark the right answer

## Options

### `quiz-2` (container)

| Option | Meaning | Default |
|---|---|---|
| `shuffle` | Randomize answer order | off |

### `quiz-answer` (nested)

| Option | Meaning | Default |
|---|---|---|
| `correct` | Mark this answer as correct | off |

## Notes

- For simple text-only quizzes, see [`quiz`](quiz.md).

## Source

[`src/munchboka_edutools/directives/quiz2.py`](https://github.com/reneaas/munchboka-edutools/blob/main/src/munchboka_edutools/directives/quiz2.py)
