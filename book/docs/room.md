# `room` directive

Defines one room inside `escape-room-2`.

## Signature

- Required arguments: `0`
- Optional arguments: `0`
- Body content: `yes`

## Options

| Option | Type |
|---|---|
| `code` | string (required) |
| `title` | string |

## Example

````markdown
::::{room}
---
code: 42
title: Warm-up
---
What is $20+22$?
::::
````

## Notes

- Must be nested inside `escape-room-2`.

## Source

`src/munchboka_edutools/directives/escape_room2.py`
