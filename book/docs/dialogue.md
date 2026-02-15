# `dialogue` directive

Creates a two-speaker chat/dialogue layout.

## Signature

- Required arguments: `0`
- Optional arguments: `0`
- Body content: `yes`

## Options

| Option | Type |
|---|---|
| `name1` | string (required) |
| `name2` | string (required) |
| `speaker1` | value |
| `speaker2` | value |

## Example

````markdown
```{dialogue}
:name1: Teacher
:name2: Student
:speaker1: left
:speaker2: right

Teacher: What is $2+2$?
Student: It is $4$.
```
````

## Source

`src/munchboka_edutools/directives/dialogue.py`
