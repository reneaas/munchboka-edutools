# `escape-room` directive

The `escape-room` directive creates a sequential puzzle flow where each room is unlocked by entering a code. Students solve puzzles to progress through rooms in order — ideal for gamified review activities.

## Basic usage

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

:::{escape-room}
Puzzle: Room 1
Code: 42
Q: What is $20+22$?

Puzzle: Room 2
Code: 144
Q: What is $12\times 12$?
:::

## Syntax overview

The content uses a plain-text format with three markers:

```
Puzzle: <room title>
Code: <unlock code>
Q: <question text>
```

- **`Puzzle:`** — starts a new room with a display title
- **`Code:`** — the answer that unlocks this room
- **`Q:`** — the question / puzzle prompt (can span multiple lines)

Rooms are displayed sequentially. The student must enter the correct code for each room before moving on.

## Options

| Option | Meaning | Default |
|---|---|---|
| `case_insensitive` | Accept codes regardless of letter case | off |

## Notes

- Aliases: `escaperoom`
- For a more modular version with nested directives, see [`escape-room-2`](escape-room-2.md).

## Source

[`src/munchboka_edutools/directives/escape_room.py`](https://github.com/reneaas/munchboka-edutools/blob/main/src/munchboka_edutools/directives/escape_room.py)
