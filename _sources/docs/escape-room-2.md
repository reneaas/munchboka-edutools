# `escape-room-2` directive

The `escape-room-2` directive is a modular version of the escape room that uses nested `room` blocks. Each room is a full directive that can contain any other content — plots, code blocks, images, and math.

## Basic usage

````markdown
:::::{escape-room-2}
::::{room}
---
code: 42
title: Room 1
---
What is $20+22$?
::::

::::{room}
---
code: 144
title: Room 2
---
What is $12\times 12$?
::::
:::::
````

:::::{escape-room-2}
::::{room}
---
code: 42
title: Room 1
---
What is $20+22$?
::::

::::{room}
---
code: 144
title: Room 2
---
What is $12\times 12$?
::::
:::::

## Syntax overview

### Structure

1. **`escape-room-2`** — outer container
2. **`room`** — one per puzzle; specifies `code` and `title` in front matter

The content inside each `room` can include any Sphinx/MyST directives.

## Options

### `escape-room-2` (container)

| Option | Meaning | Default |
|---|---|---|
| `case_insensitive` | Accept codes regardless of letter case | off |

### `room` (nested)

| Option | Meaning | Default |
|---|---|---|
| `code` | The unlock code for this room | *(required)* |
| `title` | Display title for the room | — |

## Tips

- Use `case_insensitive` when codes are text-based and you don't want case to matter.
- Each `room` block can embed plots, interactive code, images, etc.

## Source

[`src/munchboka_edutools/directives/escape_room2.py`](https://github.com/reneaas/munchboka-edutools/blob/main/src/munchboka_edutools/directives/escape_room2.py)
