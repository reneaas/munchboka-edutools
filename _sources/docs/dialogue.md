# `dialogue` directive

The `dialogue` directive creates conversation-style content with chat-bubble styling. Two speakers alternate with left/right alignment, and LaTeX math is fully supported.

## Basic usage

````markdown
```{dialogue}
:name1: Alice
:name2: Bob
:speaker1: left
:speaker2: right

Alice: Hello! How are you?
Bob: I'm doing great, thanks!
Alice: Glad to hear it.
```
````

which yields:

```{dialogue}
:name1: Alice
:name2: Bob
:speaker1: left
:speaker2: right

Alice: Hello! How are you?
Bob: I'm doing great, thanks!
Alice: Glad to hear it.
```

## Math in dialogue

LaTeX math works inside messages:

````markdown
```{dialogue}
:name1: Teacher
:name2: Student
:speaker1: left
:speaker2: right

Teacher: Can you solve $x^2 - 5x + 6 = 0$?
Student: Yes! I can factor it as $(x - 2)(x - 3) = 0$.
Teacher: What are the solutions?
Student: $x = 2$ and $x = 3$.
```
````

which yields:

```{dialogue}
:name1: Teacher
:name2: Student
:speaker1: left
:speaker2: right

Teacher: Can you solve $x^2 - 5x + 6 = 0$?
Student: Yes! I can factor it as $(x - 2)(x - 3) = 0$.
Teacher: What are the solutions?
Student: $x = 2$ and $x = 3$.
```

## Options

| Option | Type | Required | Meaning |
|---|---|---|---|
| `name1` | string | yes | Name of the first speaker |
| `name2` | string | yes | Name of the second speaker |
| `speaker1` | `left` or `right` | yes | Alignment of the first speaker |
| `speaker2` | `left` or `right` | yes | Alignment of the second speaker |

## Content format

Each line in the body should follow the pattern `SpeakerName: Message text`. Lines that do not match this pattern are ignored.

## Source

The implementation lives in `src/munchboka_edutools/directives/dialogue.py`.
