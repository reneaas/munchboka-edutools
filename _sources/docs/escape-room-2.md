# `escape-room-2` directive

Container directive for the nested Escape Room 2.0 structure.

## Signature

- Required arguments: `0`
- Optional arguments: `0`
- Body content: `yes`

## Options

| Option | Type |
|---|---|
| `case_insensitive` | flag |

## Example

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

## Notes

- Use nested `room` blocks as children.

## Source

`src/munchboka_edutools/directives/escape_room2.py`
