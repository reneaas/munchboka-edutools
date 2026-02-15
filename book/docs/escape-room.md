# `escape-room` directive

Creates a sequential puzzle flow where each room is unlocked by a code.

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
:::{escape-room}
Puzzle: Room 1
Code: 42
Q: What is $20+22$?

Puzzle: Room 2
Code: 144
Q: What is $12\times 12$?
:::
````

## Notes

- Aliases: `escaperoom`

## Source

`src/munchboka_edutools/directives/escape_room.py`
